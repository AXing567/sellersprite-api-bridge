"""
关键词板块服务层
------------------------------------------------
对应卖家精灵网页版三大能力：
  1. 关键词挖掘 / 选词     -> GET  /v2/keyword-research        （服务端渲染表格）
  2. 出单词反查 (ABA)      -> GET  /v2/aba/reverse/search/more （JSON）
  3. 关键词收录检测        -> GET  /v2/keyword-checker         （服务端渲染表格）
"""
import re
import logging
from typing import Optional, List, Dict, Any

from src.core.base_client import BaseClient
from src.core.parser import (
    pick_table, to_number, to_int, to_ratio,
)
from src.schemas.keywords import (
    KeywordResearchItem, KeywordResearchResponse,
    AbaReverseItem, AbaReverseResponse,
    KeywordReverseItem, KeywordReverseResponse,
    KeywordCheckerItem, KeywordCheckerResponse,
)

logger = logging.getLogger(__name__)

MARKETPLACE_TO_ID = {
    "US": "1", "JP": "2", "UK": "3", "DE": "4", "FR": "5",
    "IT": "6", "ES": "7", "CA": "8", "IN": "9", "MX": "10",
    "BR": "11", "AU": "12", "AE": "13", "SA": "14", "SG": "15",
    "NL": "16", "SE": "17", "PL": "18", "TR": "19", "BE": "20",
}


def _split_keyword_cell(text: str) -> tuple[str, Optional[str]]:
    """
    关键词单元格形如：'toilet paper 厕纸 Scott ComfortPlus Toilet Paper...'
    拆出：英文关键词、中文翻译
    """
    if not text:
        return "", None
    t = text.strip()

    # 1. 开头连续的 ASCII 片段即为英文关键词
    m = re.match(r"^([\x20-\x7E]+)", t)
    en = (m.group(1).strip() if m else t.strip())

    # 2. 紧随其后的中文片段作为中文翻译
    rest = t[len(m.group(1)):] if m else ""
    cn = None
    mc = re.match(r"^([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+)", rest)
    if mc:
        cn = mc.group(1).strip()

    # 英文关键词兜底：若首个 ASCII 片段异常长（含产品标题），只取前 8 个词
    if len(en.split()) > 10:
        en = " ".join(en.split()[:10])

    return en, cn


def _parse_ppc(text: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """解析 '$ 0.91 0.72 - 1.33' -> (bid, low, high)"""
    if not text:
        return None, None, None
    nums = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not nums:
        return None, None, None
    vals = [float(n) for n in nums]
    if len(vals) >= 3:
        return vals[0], vals[1], vals[2]
    if len(vals) == 2:
        return vals[0], vals[0], vals[1]
    return vals[0], None, None


def _any_int(v) -> Optional[int]:
    """容错转 int（支持 '1,234' / 1234.0 / None）"""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, (int, float)):
            return int(v)
        return to_int(str(v))
    except Exception:
        return None


def _any_float(v) -> Optional[float]:
    """容错转 float"""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        return to_number(str(v))
    except Exception:
        return None


class KeywordService(BaseClient):
    """关键词挖掘 / 出单词反查 / 收录检测"""

    RESEARCH_URL = "https://www.sellersprite.com/v2/keyword-research"
    ABA_MORE_URL = "https://www.sellersprite.com/v2/aba/reverse/search/more"
    ABA_PAGE_URL = "https://www.sellersprite.com/v2/aba/reverse/search"
    CHECKER_URL = "https://www.sellersprite.com/v2/keyword-checker"
    REVERSE_PAGE_URL = "https://www.sellersprite.com/v2/keyword-reverse"

    # 前端表单默认隐藏字段（必须携带，否则服务端渲染会走不同分支）
    BASE_FORM = {
        "supplement": "N",
        "usestatic": "R",
        "exportGkImages": "false",
        "limitUserStatic": "true",
        "adminDes": "N",
        "presetMode": "",
        "itemImageRange": "",
        "keywordBidMatchType": "",
    }

    # ==================== 2.1 关键词挖掘 ====================

    def research(
        self,
        keyword: Optional[str] = None,
        marketplace: str = "US",
        page: int = 1,
        size: int = 20,
        order_field: str = "searches",
        order_desc: bool = True,
        min_search_volume: Optional[int] = None,
        max_search_volume: Optional[int] = None,
        min_purchase_rate: Optional[float] = None,
        exclude_keywords: Optional[str] = None,
    ) -> KeywordResearchResponse:
        station = marketplace.upper()
        params: Dict[str, Any] = dict(self.BASE_FORM)
        params.update({
            "station": station,
            "marketId": MARKETPLACE_TO_ID.get(station, "1"),
            "order.field": order_field,
            "order.desc": "true" if order_desc else "false",
            "page": str(page),
            "size": str(size),
        })
        if keyword:
            params["includeKeywords"] = keyword
        if exclude_keywords:
            params["excludeKeywords"] = exclude_keywords
        if min_search_volume is not None:
            params["minSearches"] = str(min_search_volume)
        if max_search_volume is not None:
            params["maxSearches"] = str(max_search_volume)
        if min_purchase_rate is not None:
            params["minPurchaseRate"] = str(min_purchase_rate)

        resp = self.get(self.RESEARCH_URL, params=params, timeout=120,
                        headers={"Referer": self.RESEARCH_URL})

        table = pick_table(resp.text, prefer_class="js-freeze-header", min_rows=1)
        if not table:
            return KeywordResearchResponse(
                marketplace=station, keyword=keyword, page=page, size=size,
                returned=0, has_more=False, items=[],
                notice="页面未返回可解析的数据表格（可能触发风控或会员额度限制）",
            )

        items: List[KeywordResearchItem] = []
        nodes = table.get("nodes") or []

        for row_idx, row in enumerate(table["rows"]):
            if len(row) < 15:
                continue
            # 过滤「所属类目:」等分隔行
            if row[0].startswith("所属类目") or row[0].startswith("完整市场路径"):
                continue
            if not row[2] or not row[1].strip().isdigit():
                continue

            en, cn = _split_keyword_cell(row[2])

            # 用 DOM 节点精确取值（关键词 a[data-clipboard] / 中文 span.keyword-cn-color）
            if row_idx < len(nodes):
                tds = nodes[row_idx]
                if len(tds) > 2:
                    kw_a = tds[2].find("a", attrs={"data-clipboard": True})
                    if kw_a:
                        en = kw_a.get("data-clipboard") or kw_a.get_text(strip=True) or en
                    cn_span = tds[2].find("span", class_="keyword-cn-color")
                    if cn_span:
                        cn = cn_span.get_text(strip=True) or None

            search_vol = to_int(row[5].split()[0]) if row[5] else None
            purchase_cell = row[6].split() if row[6] else []
            impressions_cell = row[7].split() if row[7] else []
            yoy_cell = re.findall(r"\(([\d\.]+)%\)", row[9]) if len(row) > 9 and row[9] else []
            concell = re.findall(r"[\d\.]+%", row[10]) if len(row) > 10 and row[10] else []
            ppc_bid, ppc_low, ppc_high = _parse_ppc(row[14] if len(row) > 14 else None)
            sd_cell = row[15].split() if len(row) > 15 and row[15] else []
            market_cell = row[16] if len(row) > 16 else ""

            m_price = re.search(r"\$\s*([\d\.]+)", market_cell)
            m_sales = re.search(r"([\d,]{3,})", market_cell.replace(m_price.group(0), "") if m_price else market_cell)
            m_rating = re.search(r"\(([\d\.]+)\)", market_cell)

            items.append(KeywordResearchItem(
                rank=to_int(row[1]),
                keyword=en,
                keyword_cn=cn,
                monthly_search_volume=search_vol,
                daily_search_volume=(int(search_vol / 30) if search_vol else None),
                monthly_purchases=to_int(purchase_cell[0]) if purchase_cell else None,
                purchase_rate=to_ratio(purchase_cell[1]) if len(purchase_cell) > 1 else None,
                impressions=to_int(impressions_cell[0]) if impressions_cell else None,
                clicks=to_int(impressions_cell[1]) if len(impressions_cell) > 1 else None,
                growth_rate=to_ratio(row[8]) if len(row) > 8 and row[8] else None,
                yoy_growth_rate=(float(yoy_cell[0]) / 100.0 if yoy_cell else None),
                click_concentration=to_ratio(concell[0]) if concell else None,
                aba_rank=to_int(row[11]) if len(row) > 11 else None,
                traffic_value=to_number(row[12]) if len(row) > 12 else None,
                ppc_bid=ppc_bid,
                ppc_bid_low=ppc_low,
                ppc_bid_high=ppc_high,
                supply_demand_ratio=to_number(sd_cell[0]) if sd_cell else None,
                product_count=to_int(sd_cell[1]) if len(sd_cell) > 1 else None,
                market_avg_price=float(m_price.group(1)) if m_price else None,
                market_monthly_sales=int(m_sales.group(1).replace(",", "")) if m_sales else None,
                market_avg_rating=float(m_rating.group(1)) if m_rating else None,
                sample_product_title=(row[3] or None),
            ))

        notice = None
        if not items:
            notice = ("未解析到关键词数据。该页面需要有效会员额度，"
                      "若网页端同样查不到数据，请确认会员套餐是否包含关键词挖掘次数。")

        # 官网对 size 参数不敏感（固定返回整页），此处按调用方要求本地截断
        has_more = len(items) >= size
        sliced = items[:size]

        return KeywordResearchResponse(
            marketplace=station,
            keyword=keyword,
            page=page,
            size=size,
            returned=len(sliced),
            has_more=has_more,
            items=sliced,
            notice=notice,
        )

    # ==================== 2.2 出单词反查 (ABA) ====================

    def _resolve_aba_tables(self, station: str) -> tuple[str, str]:
        """从 ABA 页面读取当前可用的周表与月表标识"""
        try:
            resp = self.get(self.ABA_PAGE_URL, params={"station": station}, timeout=90,
                            headers={"Referer": self.ABA_PAGE_URL})
            weekly = sorted(set(re.findall(r"ara_\d{8}", resp.text)))
            monthly = sorted(set(re.findall(r"ara_\d{6}", resp.text)))
            table = weekly[-1] if weekly else "ara_20261017"
            mtable = monthly[-1] if monthly else table[:7]
            return table, mtable
        except Exception as e:
            logger.warning(f"读取 ABA 表名失败，使用默认值: {e}")
            return "ara_20261017", "ara_202610"

    def aba_reverse(
        self,
        asin: str,
        marketplace: str = "US",
        order_field: str = "searchRank",
    ) -> AbaReverseResponse:
        station = marketplace.upper()
        table, mtable = self._resolve_aba_tables(station)

        params = {
            "station": station,
            "table": table,
            "monthlyTable": mtable,
            "asin": asin.strip().upper(),
            "order.field": order_field,
            "order.desc": "false",
            "reverseType": "monthly",
            "conversionType": "",
            "loadVariations": "false",
        }
        resp = self.get(self.ABA_MORE_URL, params=params, timeout=150,
                        headers={
                            "Referer": f"{self.ABA_PAGE_URL}?asin={asin}&station={station}",
                            "X-Requested-With": "XMLHttpRequest",
                        })

        items: List[AbaReverseItem] = []
        try:
            payload = resp.json()
        except Exception:
            return AbaReverseResponse(
                asin=asin, marketplace=station, table_period=table,
                total=0, returned=0, items=[],
                notice="ABA 接口返回非 JSON 内容，可能存在风控拦截",
            )

        data = payload.get("data") or payload.get("dto") or {}
        raw_items = data.get("items") or []
        total = data.get("total") or len(raw_items)

        for it in raw_items:
            kw = (it.get("keyword") or it.get("keywords") or "").strip()
            if not kw:
                continue
            if len(kw) > 120:  # 亚马逊有时把商品标题当作搜索词，过长则截断
                kw = kw[:120].rstrip() + "..."
            items.append(AbaReverseItem(
                keyword=kw,
                search_frequency_rank=it.get("searchRank") or it.get("rank"),
                click_share=it.get("clickShareRate") or it.get("clicksShare"),
                conversion_share=it.get("conversionShareRate") or it.get("cvsShareRate"),
                search_volume=it.get("searches") or it.get("searchVolume"),
                organic_rank=it.get("organicRank") or it.get("rankOrganic"),
                sponsored_rank=it.get("adRank") or it.get("rankSponsored"),
            ))

        notice = None
        if not items:
            notice = (
                f"该 ASIN 在 {table} 周期内未取到 ABA 出单词数据。常见原因："
                "① 该 ASIN 当月无 ABA 收录；② 会员套餐不含出单词反查额度；"
                "③ 该 ASIN 所属变体/站点无数据。建议先在网页端确认同参数能否查到。"
            )

        return AbaReverseResponse(
            asin=asin, marketplace=station, table_period=table,
            total=int(total or 0), returned=len(items), items=items, notice=notice,
        )

    # ==================== 2.3 关键词反查（ASIN -> 全量关键词） ====================

    # 反查页 JSON 的字段名在不同版本间有差异，这里做多别名兜底
    _REV_KEY_ALIASES = {
        "keyword": ("keywords", "keyword", "keywordText"),
        "keyword_cn": ("keywordCn", "keyword_cn", "keywordTranslate"),
        "search_rank": ("searchRank", "rank", "abaRank"),
        "searches": ("searches", "searchVolume", "monthlySearches"),
        "clicks": ("clicks", "clickCount"),
        "impressions": ("impressions", "impressionCount"),
        "click_share": ("clickShareRate", "clicksShare", "clickShare"),
        "conversion_share": ("conversionShareRate", "cvsShareRate", "conversionShare"),
        "purchase_rate": ("purchaseRate", "cvr"),
        "purchases": ("purchases", "purchaseCount"),
        "organic_rank": ("rankOrganic", "organicRank", "naturalRank", "rankOrigin"),
        "sponsored_rank": ("adRank", "rankSponsored", "sponsoredRank"),
    }

    @classmethod
    def _pick(cls, item: Dict[str, Any], field: str):
        for k in cls._REV_KEY_ALIASES.get(field, ()):
            if k in item and item[k] not in (None, "", []):
                return item[k]
        return None

    def _reverse_primary(
        self, asin: str, station: str, size: int, max_pages: int = 3
    ) -> tuple[List[KeywordReverseItem], int, str]:
        """
        主通道：网页版「关键词反查」AJAX 接口
        GET /v2/keyword-reverse/{station}/{asin}/more?pageNum=N&v=false

        注意：该接口对「会员套餐不含关键词反查权益」的账号会返回
        dto.station=GLOBAL、dto.total=0、dto.items=[] 的空结果（不是报错），
        调用方需据此自动降级到 ABA 通道。
        """
        items: List[KeywordReverseItem] = []
        total = 0
        page = 1
        while page <= max_pages and len(items) < size:
            url = f"{self.REVERSE_PAGE_URL}/{station}/{asin}/more"
            try:
                resp = self.get(url, params={"pageNum": page, "v": "false"}, timeout=150,
                                headers={
                                    "Referer": f"{self.REVERSE_PAGE_URL}/{station}/{asin}",
                                    "X-Requested-With": "XMLHttpRequest",
                                    "Accept": "application/json, text/javascript, */*; q=0.01",
                                })
                payload = resp.json()
            except Exception as e:
                logger.warning(f"关键词反查主通道失败(第{page}页): {e}")
                break

            dto = payload.get("dto") or payload.get("data") or {}
            if not isinstance(dto, dict):
                break
            total = int(dto.get("total") or total or 0)
            raw = dto.get("items") or []
            if not raw:
                break

            for it in raw:
                kw = (self._pick(it, "keyword") or "").strip()
                if not kw:
                    continue
                items.append(KeywordReverseItem(
                    keyword=kw[:160],
                    keyword_cn=self._pick(it, "keyword_cn"),
                    search_rank=_any_int(self._pick(it, "search_rank")),
                    searches=_any_int(self._pick(it, "searches")),
                    clicks=_any_int(self._pick(it, "clicks")),
                    impressions=_any_int(self._pick(it, "impressions")),
                    click_share=_any_float(self._pick(it, "click_share")),
                    conversion_share=_any_float(self._pick(it, "conversion_share")),
                    purchase_rate=_any_float(self._pick(it, "purchase_rate")),
                    purchases=_any_int(self._pick(it, "purchases")),
                    organic_rank=_any_int(self._pick(it, "organic_rank")),
                    sponsored_rank=_any_int(self._pick(it, "sponsored_rank")),
                ))
            page += 1

        return items, total, ""

    def reverse(
        self,
        asin: str,
        marketplace: str = "US",
        size: int = 50,
        max_pages: int = 3,
        include_aba_fallback: bool = True,
    ) -> KeywordReverseResponse:
        """
        「关键词反查」：输入 ASIN，返回给它带来曝光/出单的关键词全集。

        双通道设计（自动降级）：
          主通道  /v2/keyword-reverse/{站点}/{ASIN}/more   —— 网页版关键词反查
          备通道  /v2/aba/reverse/search/more             —— ABA 出单词反查

        主通道返回空（常见于试用/免费账号无该模块权益）时自动切备通道，
        返回体用 `source` 字段标明实际数据来源，调用方无需感知差异。
        """
        station = marketplace.upper()
        asin = asin.strip().upper()

        items, total, _ = self._reverse_primary(asin, station, size, max_pages)
        source = "keyword-reverse"
        period = None
        notice = None

        if not items and include_aba_fallback:
            try:
                aba = self.aba_reverse(asin=asin, marketplace=station)
                source = "aba-reverse"
                period = aba.table_period
                total = aba.total
                items = [KeywordReverseItem(
                    keyword=a.keyword,
                    search_rank=a.search_frequency_rank,
                    searches=a.search_volume,
                    click_share=a.click_share,
                    conversion_share=a.conversion_share,
                    organic_rank=a.organic_rank,
                    sponsored_rank=a.sponsored_rank,
                ) for a in aba.items]
                if items:
                    notice = ("主通道「关键词反查」返回空结果（多为账号套餐不含该模块权益），"
                              "已自动降级到「ABA 出单词反查」通道，数据为官方 ABA 口径，"
                              "字段差异：无逐词自然排名、关键词可能被 ABA 截断。")
            except Exception as e:
                logger.warning(f"ABA 降级通道也失败: {e}")

        if not items:
            notice = (notice or "") + (
                " 两个通道均无数据。请确认：① ASIN 有效且属于该站点；"
                "② 账号「关键词反查 / 出单词反查」剩余额度（试用账号通常不含该权益）；"
                "③ 该 ASIN 当月确实无搜索曝光。"
            )

        sliced = items[:size]
        return KeywordReverseResponse(
            asin=asin, marketplace=station, source=source, period=period,
            total=int(total or len(items)), returned=len(sliced),
            items=sliced, notice=notice or None,
        )

    # ==================== 2.4 关键词收录检测 ====================

    @staticmethod
    def _norm_kw(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").lower()).strip()

    def checker(
        self,
        asin: str,
        keywords: List[str],
        marketplace: str = "US",
    ) -> KeywordCheckerResponse:
        """
        「关键词收录检测」：判断某个 ASIN 是否被指定关键词收录。

        实现说明（重要）：
          网页版该功能的接口为两步式（POST 建任务拿 flag -> 轮询 result/{flag}），
          且 `/v2/keyword-checker/*` 子路由在未开通该权益的账号下直接 404，
          无法稳定抓取。因此这里改为「反查命中判定」：
          调 reverse() 拿到该 ASIN 的全部曝光关键词（主通道为空则自动走 ABA），
          再逐个比对调用方传入的关键词——命中即视为已收录，并回填该词的排名/份额。

        口径差异：命中判定基于「该 ASIN 在该词下有曝光数据」，
        而非实时抓取亚马逊搜索页的物理位次，因此 organic_rank 可能为空。
        `evidence` 字段会写清每个词的判定依据。
        """
        station = marketplace.upper()
        asin = asin.strip().upper()
        want = [k.strip() for k in keywords if k and k.strip()]

        rev = self.reverse(asin=asin, marketplace=station,
                           size=max(200, len(want) * 4), max_pages=3)

        # 建立索引：精确词 -> 条目；同时保留列表用于包含匹配
        exact: Dict[str, KeywordReverseItem] = {}
        for it in rev.items:
            exact.setdefault(self._norm_kw(it.keyword), it)

        items: List[KeywordCheckerItem] = []
        for kw in want:
            n = self._norm_kw(kw)
            hit = exact.get(n)
            evidence = None

            if hit is None and len(n) >= 4:
                # 包含匹配：ABA 关键词常被截断或更长，允许双向包含
                for it in rev.items:
                    cand = self._norm_kw(it.keyword)
                    if n in cand or (len(cand) >= 4 and cand in n):
                        hit = it
                        evidence = f"模糊命中：{it.keyword[:80]}"
                        break

            if hit is not None:
                organic = hit.organic_rank
                sponsored = hit.sponsored_rank
                items.append(KeywordCheckerItem(
                    keyword=kw,
                    is_indexed=True,
                    is_organic_indexed=bool(organic),
                    organic_rank=organic,
                    is_sponsored_indexed=bool(sponsored),
                    sponsored_rank=sponsored,
                    page_no=(int(organic / 48) + 1) if organic else None,
                    evidence=evidence or f"命中：{hit.keyword[:80]}"
                                         f"（ABA排名 {hit.search_rank or '-'}）",
                ))
            else:
                items.append(KeywordCheckerItem(
                    keyword=kw,
                    is_indexed=False,
                    is_organic_indexed=False,
                    is_sponsored_indexed=False,
                    evidence="未在反查结果中出现；若确认该词有曝光，可能是数据周期未覆盖或关键词拼写不一致",
                ))

        notice = None
        if not rev.items:
            notice = ("反查通道无数据，收录判定无法进行，全部按「未收录」返回。"
                      "请先解决反查数据问题（换用含关键词反查/出单词反查权益的账号）。")
        elif all(not i.organic_rank for i in items):
            notice = ("判定口径：基于「该 ASIN 在该关键词下有曝光数据」判定收录，"
                      "当前数据源未提供逐词自然排名，故 organic_rank 为空；"
                      "若需要物理位次，请在网页版「关键词收录检测」直接查看。")

        return KeywordCheckerResponse(
            asin=asin,
            marketplace=station,
            source=rev.source,
            checked=len(items),
            indexed_count=sum(1 for i in items if i.is_indexed),
            items=items,
            notice=notice or rev.notice,
        )
