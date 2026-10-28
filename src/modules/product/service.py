"""
选产品 / 选市场服务层
------------------------------------------------
  1. 产品库多维度选品  -> GET /v2/product-research/monthly
  2. 细分市场分析      -> GET /v2/market-research

【选产品关键要点（踩坑记录）】
  · 端点必须带 /monthly 后缀，`/v2/product-research` 只是入口页。
  · 必须用 GET + nodeIdPath（冒号分隔的完整类目路径），只传 nodeId 会拿不到数据。
  · `order.field` 是**枚举值**，不是自由文本：传了非法值（如 units）服务端不报错，
    直接返回「暂无结果」空页——这是最容易误判成"接口不通"的坑。
    合法值只有：total_units / total_amount / bsr_rank / price / rating / profit。
  · 页面 <tr> 未正确嵌套在 <tbody> 内，常规 tbody 遍历只能拿到 1 行，
    必须用 extract_rows_loose() 正则扫全文重建行。
  · 列位置固定 14 列（见 _COL_* 常量），但仍保留表头校验以应对官网改版。
"""
import re
import logging
from typing import Optional, List, Dict, Any

from src.core.base_client import BaseClient
from src.core.parser import (
    extract_rows_loose, find_col, to_number, to_int, to_ratio, cell,
)
from src.schemas.product import (
    ProductItem, ProductFilterResponse,
    MarketItem, MarketResearchResponse,
)

logger = logging.getLogger(__name__)

MARKETPLACE_TO_ID = {
    "US": "1", "JP": "2", "UK": "3", "DE": "4", "FR": "5",
    "IT": "6", "ES": "7", "CA": "8", "IN": "9", "MX": "10",
    "BR": "11", "AU": "12", "AE": "13", "SA": "14", "SG": "15",
}

ASIN_RE = re.compile(r"\b(B0[A-Z0-9]{8})\b")
PASIN_RE = re.compile(r"PASIN\s*[:：]\s*([A-Z0-9]{10})")
BADGE_TOKENS = {"A+", "V", "BS", "AC", "NR", "NEW"}

# ---- 选产品固定列位置（表头顺序，官网改版时用 _validate_headers 报警）----
_COL_RANK = 0
_COL_BADGE = 1
_COL_INFO = 2
_COL_BSR = 3
_COL_TREND = 4
_COL_SALES = 5
_COL_REVENUE = 6
_COL_PRICE = 7
_COL_MARGIN = 8
_COL_REVIEWS = 9
_COL_RATING = 10
_COL_DATE = 11
_COL_DELIVERY = 12

_EXPECT_HEADERS = ["#", "", "产品信息", "BSR", "销量趋势", "销量", "销售额",
                   "价格", "毛利率", "评分数", "评分", "上架时间", "配送"]

# ---- 排序字段：对外友好名 -> 官网枚举值 ----
ORDER_FIELD_MAP = {
    "units": "total_units", "sales": "total_units", "月销量": "total_units",
    "total_units": "total_units",
    "revenue": "total_amount", "amount": "total_amount", "销售额": "total_amount",
    "total_amount": "total_amount",
    "bsr": "bsr_rank", "rank": "bsr_rank", "bsr_rank": "bsr_rank",
    "price": "price", "价格": "price",
    "rating": "rating", "评分": "rating",
    "profit": "profit", "margin": "profit", "毛利": "profit", "毛利率": "profit",
}


def _kv(text: str, key: str) -> Optional[float]:
    """从 '商品: 100 品牌: 17' 中取某个 key 的数值"""
    if not text:
        return None
    m = re.search(rf"{key}\s*[:：]\s*([\d\.,]+)", text)
    return to_number(m.group(1)) if m else None


def _pct(text: str, key: Optional[str] = None) -> Optional[float]:
    """提取百分比，key 为空则取第一个；返回 0~1 小数"""
    if not text:
        return None
    if key:
        m = re.search(rf"{key}\s*[:：]\s*(-?[\d\.]+)%", text)
        return round(float(m.group(1)) / 100.0, 4) if m else None
    m = re.search(r"(-?[\d\.]+)%", text)
    return round(float(m.group(1)) / 100.0, 4) if m else None


def _split_tiers(text: Optional[str]) -> List[str]:
    """把复合单元格 '3,404 33%' 拆成 ['3,404', '33%']"""
    if not text:
        return []
    return [p for p in re.split(r"[\s\n]+", text.strip()) if p]


def _norm_month(month: Optional[str]) -> str:
    """
    月份参数归一化：
      空 / nearly / 近期        -> bsr_sales_nearly
      YYYYMM / 带横线           -> bsr_sales_monthly_YYYYMM
    """
    if not month:
        return "bsr_sales_nearly"
    m = str(month).strip()
    if m in ("nearly", "近30天", "最近30天", "bsr_sales_nearly"):
        return "bsr_sales_nearly"
    if m.startswith("bsr_sales_monthly_"):
        return m
    digits = re.sub(r"[^0-9]", "", m)
    if len(digits) == 6:
        return f"bsr_sales_monthly_{digits}"
    return "bsr_sales_nearly"


def _attach_path_metrics(item: "MarketItem", text: str, td=None) -> None:
    """
    解析「完整市场路径」展开行里携带的类目深度指标：
    英文/中文路径、nodeIdPath、A+ 占比、新品均值、平均重量体积、平均毛利率、
    卖家所属地、搜索购买比。

    注意：nodeIdPath 只存在于 <a href> 里，纯文本取不到，必须传 td 节点。
    """
    m = re.search(r"完整市场路径\s*[:：]\s*(.+?)(?:\s*市场路径|\s*市场分析|$)", text)
    if m:
        item.market_path = m.group(1).strip()[:300]
    else:
        item.market_path = text.split(":", 1)[-1].strip()[:300]

    m = re.search(r"市场路径\s*\(中文\)\s*[:：]\s*(.+?)(?:\s*A\+数量占比|$)", text)
    if m:
        item.market_path_cn = m.group(1).strip()[:300]

    def grab(pattern: str) -> Optional[str]:
        mm = re.search(pattern, text)
        return mm.group(1) if mm else None

    item.aplus_ratio = to_ratio(grab(r"A\+数量占比\s*[:：]\s*([\d\.]+)%"))
    item.new_avg_ratings = to_int(grab(r"新品平均评分数\s*[:：]\s*([\d,\.]+)"))
    item.new_avg_price = to_number(grab(r"新品平均价格\s*[:：]\s*\$?\s*([\d,\.]+)"))
    item.new_avg_rating = to_number(grab(r"新品平均星级\s*[:：]\s*([\d\.]+)"))
    item.new_avg_sales = to_int(grab(r"新品月均销量\s*[:：]\s*([\d,\.]+)"))
    item.new_avg_revenue = to_number(grab(r"新品月均销售额\s*[:：]\s*\$?\s*([\d,\.]+)"))
    item.avg_weight_pounds = to_number(grab(r"平均重量\s*[:：]\s*([\d\.]+)\s*pounds"))
    item.avg_volume_inch3 = to_number(grab(r"平均体积\s*[:：]\s*([\d,\.]+)\s*in"))
    item.avg_gross_margin = to_ratio(grab(r"平均毛利率\s*[:：]\s*([\d\.]+)%"))
    item.china_seller_ratio = to_ratio(grab(r"卖家所属地\s*[:：][^|]*\|\s*([\d\.]+)%"))
    item.search_purchase_ratio = grab(r"搜索购买比\s*[:：]\s*([^\s|]+)")

    # nodeIdPath 只在 href 里，且同一行会从大类逐级列出多条，取层级最深（细分市场自己）那条
    paths: List[str] = []
    if td is not None:
        for a in td.find_all("a"):
            pm = re.search(r"nodeIdPath=([\d:]+)", a.get("href", "") or "")
            if pm:
                paths.append(pm.group(1))
    if not paths:
        paths = re.findall(r"nodeIdPath=([\d:]+)", text)
    if paths:
        deepest = max(paths, key=lambda p: p.count(":"))
        item.node_id_path = deepest
        item.node_id = deepest.split(":")[-1]
    else:
        mn = re.search(r"nodeId[=/](\d+)", text)
        if mn:
            item.node_id = mn.group(1)


class ProductService(BaseClient):
    PRODUCT_URL = "https://www.sellersprite.com/v2/product-research/monthly"
    MARKET_URL = "https://www.sellersprite.com/v2/market-research"

    # 官网「选产品」表单的固定隐藏域（缺了会被当成非法请求）
    BASE_FORM = {
        "selectType": "1",
        "weightUnit": "g",
        "filterSub": "false",
        "presetMode": "",
        "symbol": "",
        "type": "monthly",
        "months": "",
        "showMode": "",
        "smallAndLight": "",
        "allChecked": "false",
    }

    # ==================== 3.1 产品库多维度选品 ====================

    def filter_products(
        self,
        marketplace: str = "US",
        page: int = 1,
        size: int = 20,
        node_id_path: Optional[str] = None,
        month: Optional[str] = None,
        order_field: str = "units",
        order_desc: bool = True,
        # ---- 商品属性筛选 ----
        min_sales: Optional[int] = None,
        max_sales: Optional[int] = None,
        min_revenue: Optional[float] = None,
        max_revenue: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        min_ratings: Optional[int] = None,
        max_ratings: Optional[int] = None,
        min_profit: Optional[float] = None,
        max_profit: Optional[float] = None,
        min_bsr: Optional[int] = None,
        max_bsr: Optional[int] = None,
        min_qa: Optional[int] = None,
        max_qa: Optional[int] = None,
        min_variations: Optional[int] = None,
        max_variations: Optional[int] = None,
        min_fba_fee: Optional[float] = None,
        max_fba_fee: Optional[float] = None,
        seller_type: Optional[str] = None,
        seller_nation: Optional[str] = None,
        keyword: Optional[str] = None,
        exclude_keyword: Optional[str] = None,
        best_seller_only: bool = False,
        new_release_only: bool = False,
    ) -> ProductFilterResponse:
        """
        参数名与官网「选产品」筛选面板一一对应（已从表单实测校准）：
          minSales/maxSales        近30天销量
          minAmount/maxAmount      近30天销售额
          minRanking/maxRanking    大类 BSR
          minReviews/maxReviews    累计评分数
          minReviewRating/...      评分星级
          minProfit/maxProfit      毛利率（整数百分比，如 30 表示 30%）
          minQuestions/maxQuestions Q&A 数
          minVariations/...        变体数
          minFba/maxFba            FBA 运费
          keywords / outOfKeywords 标题关键词包含 / 排除
          sellerType               AMZ / FBA / FBM
          sellerNations            卖家所属地，如 CN
          bestSeller / newRelease  徽章筛选
        """
        station = marketplace.upper()
        market_id = MARKETPLACE_TO_ID.get(station, "1")
        month_name = _norm_month(month)

        of = ORDER_FIELD_MAP.get(str(order_field).lower(), None)
        if of is None:
            of = ORDER_FIELD_MAP.get(str(order_field), "total_units")

        params: Dict[str, Any] = dict(self.BASE_FORM)
        params.update({
            "marketId": market_id,
            "station": station,
            "monthName": month_name,
            "page": str(page),
            "size": str(size),
            "order.field": of,
            "order.desc": "true" if order_desc else "false",
        })
        if node_id_path:
            params["nodeIdPath"] = node_id_path.strip()

        # ---- 数值型筛选 ----
        numeric = {
            "minSales": min_sales, "maxSales": max_sales,
            "minAmount": min_revenue, "maxAmount": max_revenue,
            "minRanking": min_bsr, "maxRanking": max_bsr,
            "minReviews": min_ratings, "maxReviews": max_ratings,
            "minReviewRating": min_rating, "maxReviewRating": max_rating,
            "minProfit": min_profit, "maxProfit": max_profit,
            "minQuestions": min_qa, "maxQuestions": max_qa,
            "minVariations": min_variations, "maxVariations": max_variations,
            "minFba": min_fba_fee, "maxFba": max_fba_fee,
            "minPrice": min_price, "maxPrice": max_price,
        }
        for k, v in numeric.items():
            if v is not None:
                params[k] = str(v)

        # ---- 字符串型筛选 ----
        if seller_type:
            st = seller_type.upper()
            params["sellerType"] = st
            params["sellerTypes"] = st
        if seller_nation:
            params["sellerNations"] = seller_nation.upper()
            params["sellerNationTypesCheck"] = "true"
        if keyword:
            params["keywords"] = keyword
        if exclude_keyword:
            params["outOfKeywords"] = exclude_keyword
        if best_seller_only:
            params["bestSeller"] = "true"
        if new_release_only:
            params["newRelease"] = "true"

        resp = self.get(self.PRODUCT_URL, params=params, timeout=180,
                        headers={"Referer": "https://www.sellersprite.com/v2/product-research"})
        html = resp.text

        headers, rows, nodes = extract_rows_loose(html, min_cells=8)
        items: List[ProductItem] = []
        notice: Optional[str] = None

        if headers:
            self._warn_header_drift(headers)

        for idx, row in enumerate(rows):
            item = self._parse_row(row, nodes[idx] if idx < len(nodes) else None)
            if item is not None:
                items.append(item)

        if not items:
            if "暂无结果" in html:
                notice = (
                    "该筛选条件下官网返回「暂无结果」。常见原因："
                    "1) node_id_path 不存在或该节点下无商品；"
                    "2) 筛选条件过严（毛利率/销量区间等）；"
                    "3) order_field 非法。"
                )
            else:
                notice = "未解析到商品行，可能页面结构变更或会员额度不足，请先在网页端同条件验证。"

        # 官网对 size 参数不敏感（固定按 20/50/100 整页返回），此处按调用方要求本地截断
        sliced = items[:size]
        return ProductFilterResponse(
            marketplace=station, month_name=month_name, order_field=of,
            page=page, size=size,
            returned=len(sliced), has_more=len(items) >= size,
            items=sliced, notice=notice,
        )

    # ---------- 单行解析 ----------

    @staticmethod
    def _warn_header_drift(headers: List[str]) -> None:
        """表头漂移检测：官网改列序时提前发现，避免字段错位"""
        for i, expect in enumerate(_EXPECT_HEADERS):
            if i >= len(headers):
                break
            if expect and expect not in headers[i]:
                logger.warning("选产品表头疑似漂移: 第%d列 期望含 %r 实际 %r",
                               i, expect, headers[i])
                break

    @staticmethod
    def _parse_row(row: List[str], tds: Optional[list]) -> Optional[ProductItem]:
        if not row or len(row) < 8:
            return None

        # --- 产品信息列：标题/ASIN/品牌 ---
        info_text = cell(row, _COL_INFO) or ""
        asin = None
        title = None
        brand = None

        if tds and len(tds) > _COL_INFO:
            td = tds[_COL_INFO]
            a_dp = td.find("a", href=re.compile(r"/dp/"))
            if a_dp:
                m = re.search(r"/dp/([A-Z0-9]{10})", a_dp.get("href", ""))
                asin = m.group(1) if m else None
            h1 = td.find(attrs={"title": True})
            if h1:
                title = h1.get("title")
            if not title:
                h1 = td.find(class_="h-1")
                if h1:
                    title = h1.get_text(" ", strip=True)
            a_store = td.find("a", href=re.compile(r"/stores/|/seller/|/s\?me="))
            if a_store:
                brand = a_store.get_text(strip=True)

        if not asin:
            m = ASIN_RE.search(info_text)
            asin = m.group(1) if m else None
        if not asin:
            return None

        if not title:
            t = re.sub(r"\s*ASIN\s*[:：].*$", "", info_text).strip()
            title = t or None
        if len(title or "") < 2:
            title = None
        if not brand:
            pm = PASIN_RE.search(info_text)
            tail = info_text
            if pm:
                tail = info_text[pm.end():]
            brand = tail.strip() or None
            if brand and len(brand) > 60:
                brand = brand[:60]

        parent_asin = None
        pm = PASIN_RE.search(info_text)
        if pm:
            parent_asin = pm.group(1)

        # --- 徽章 ---
        badges = [t for t in _split_tiers(cell(row, _COL_BADGE)) if t in BADGE_TOKENS] \
            or _split_tiers(cell(row, _COL_BADGE))

        # --- BSR：排名 + 变化数 + 变化率 ---
        bsr_t = _split_tiers(cell(row, _COL_BSR))
        bsr_rank = to_int(bsr_t[0]) if bsr_t else None
        bsr_growth = to_int(bsr_t[1]) if len(bsr_t) > 1 else None
        bsr_growth_rate = to_ratio(bsr_t[2]) if len(bsr_t) > 2 else None

        # --- 近30天销量 / 销售额 ---
        sales_t = _split_tiers(cell(row, _COL_SALES))
        rev_t = _split_tiers(cell(row, _COL_REVENUE))
        price_t = _split_tiers(cell(row, _COL_PRICE))
        margin_t = _split_tiers(cell(row, _COL_MARGIN))
        rev_cnt_t = _split_tiers(cell(row, _COL_REVIEWS))
        rating_t = _split_tiers(cell(row, _COL_RATING))
        date_t = _split_tiers(cell(row, _COL_DATE))
        delivery_t = _split_tiers(cell(row, _COL_DELIVERY))

        return ProductItem(
            rank=to_int(cell(row, _COL_RANK)),
            asin=asin,
            parent_asin=parent_asin,
            title=title,
            image_url=None,
            brand=brand,
            badges=badges or None,
            price=to_number(price_t[0]) if price_t else None,
            qa_count=to_int(price_t[1]) if len(price_t) > 1 else None,
            bsr_rank=bsr_rank,
            bsr_growth=bsr_growth,
            bsr_growth_rate=bsr_growth_rate,
            monthly_sales=to_int(sales_t[0]) if sales_t else None,
            sales_growth=to_ratio(sales_t[1]) if len(sales_t) > 1 else None,
            monthly_revenue=to_number(rev_t[0]) if rev_t else None,
            revenue_growth=to_ratio(rev_t[1]) if len(rev_t) > 1 else None,
            gross_margin=to_ratio(margin_t[0]) if margin_t else None,
            fba_fee=to_number(margin_t[1]) if len(margin_t) > 1 else None,
            ratings_count=to_int(rev_cnt_t[0]) if rev_cnt_t else None,
            review_rate=to_ratio(rev_cnt_t[1]) if len(rev_cnt_t) > 1 else None,
            rating=to_number(rating_t[0]) if rating_t else None,
            rating_monthly_new=to_int(rating_t[1]) if len(rating_t) > 1 else None,
            release_date=date_t[0] if date_t else None,
            listing_age=date_t[1] if len(date_t) > 1 else None,
            seller_type=delivery_t[0] if delivery_t else None,
            buyer_shipping_fee=to_number(delivery_t[1]) if len(delivery_t) > 1 else None,
        )

    # ==================== 3.2 细分市场分析 ====================

    def research_market(
        self,
        marketplace: str = "US",
        page: int = 1,
        size: int = 20,
        order_field: str = "units",
        order_desc: bool = True,
        node_id: Optional[str] = None,
    ) -> MarketResearchResponse:
        station = marketplace.upper()
        params: Dict[str, Any] = dict(self.BASE_FORM)
        params.update({
            "station": station,
            "marketId": MARKETPLACE_TO_ID.get(station, "1"),
            "order.field": ORDER_FIELD_MAP.get(str(order_field).lower(), "total_units"),
            "order.desc": "true" if order_desc else "false",
            "page": str(page),
            "size": str(size),
        })
        if node_id:
            params["nodeId"] = node_id
            params["nodeIdPath"] = node_id

        resp = self.get(self.MARKET_URL, params=params, timeout=180,
                        headers={"Referer": self.MARKET_URL})

        # min_cells 必须为 1：细分类目「完整市场路径」展开行是 <td colspan="15"> 单单元格，
        # 若按数据行的列数阈值过滤，整行深度指标（毛利率/A+/中国卖家占比）会被丢掉。
        headers, rows, nodes = extract_rows_loose(resp.text, min_cells=1)
        items: List[MarketItem] = []
        notice = None

        for idx, row in enumerate(rows):
            if not row:
                continue

            # 路径行：完整市场路径: A › B › C ... 携带大量类目深度指标
            if row[0].startswith("完整市场路径") or "完整市场路径" in row[0]:
                if items:
                    td0 = None
                    if idx < len(nodes) and nodes[idx]:
                        td0 = nodes[idx][0]
                    _attach_path_metrics(items[-1], row[0], td0)
                continue

            if len(row) < 13:
                continue
            if not row[0].strip().isdigit():
                continue

            # 市场名与节点 ID 从 DOM 精确取
            name = None
            node = None
            node_path = None
            if idx < len(nodes):
                tds = nodes[idx]
                if len(tds) > 1:
                    first = tds[1]
                    a = first.find("a")
                    if a:
                        name = a.get_text(" ", strip=True)
                        href = a.get("href", "")
                        mp = re.search(r"nodeIdPath=([\d:]+)", href)
                        if mp:
                            node_path = mp.group(1)
                            node = node_path.split(":")[-1]
                        else:
                            mn = (re.search(r"nodeId[=/](\d+)", href)
                                  or re.search(r"/(\d{5,})", href))
                            node = mn.group(1) if mn else None
            if not name:
                name = row[1].split("第1名")[0].strip() or row[1][:40]

            sales_cell = row[4].split() if row[4] else []
            rev_cell = row[5].split() if row[5] else []
            rating_cell = row[6].split() if row[6] else []
            bsr_cell = row[7].split() if row[7] else []
            seller_cell = row[8].split() if row[8] else []
            new_cell = row[11].split() if row[11] else []
            ret_cell = row[13].split() if len(row) > 13 and row[13] else []

            m_price = re.search(r"\$\s*([\d\.,]+)", row[8] or "")
            m_ret = re.findall(r"([\d\.]+)%", (row[13] if len(row) > 13 else "") or "")

            items.append(MarketItem(
                rank=to_int(row[0]),
                market_name=name,
                sample_product_count=to_int(_kv(row[2], "商品")),
                brand_count=to_int(_kv(row[2], "品牌")),
                seller_count=to_int(_kv(row[2], "卖家")),
                monthly_sales_total=to_int(row[3]),
                monthly_sales_avg=to_int(sales_cell[0]) if sales_cell else None,
                monthly_sales_avg_top=to_int(sales_cell[1]) if len(sales_cell) > 1 else None,
                monthly_revenue_avg=to_number(rev_cell[0]) if rev_cell else None,
                monthly_revenue_avg_top=to_number(rev_cell[1]) if len(rev_cell) > 1 else None,
                avg_ratings_count=to_int(rating_cell[0]) if rating_cell else None,
                avg_rating=to_number(rating_cell[1]) if len(rating_cell) > 1 else None,
                avg_bsr=to_int(bsr_cell[0]) if bsr_cell else None,
                avg_bsr_top=to_int(bsr_cell[1]) if len(bsr_cell) > 1 else None,
                avg_seller_num=to_number(seller_cell[0]) if seller_cell else None,
                avg_price=to_number(m_price.group(1)) if m_price else None,
                fba_ratio=_pct(row[9], "FBA"),
                amz_ratio=_pct(row[9], "AMZ"),
                fbm_ratio=_pct(row[9], "FBM"),
                product_monopoly_ratio=_pct(row[10], "商品"),
                brand_monopoly_ratio=_pct(row[10], "品牌"),
                seller_monopoly_ratio=_pct(row[10], "卖家"),
                new_product_count=to_int(new_cell[0]) if new_cell else None,
                new_product_ratio=to_ratio(new_cell[1]) if len(new_cell) > 1 else None,
                total_product_count=to_int(row[12]),
                return_rate=(float(m_ret[0]) / 100.0 if len(m_ret) > 0 else None),
                category_avg_return_rate=(float(m_ret[1]) / 100.0 if len(m_ret) > 1 else None),
                node_id=node,
                node_id_path=node_path,
            ))

        if not items:
            notice = "未解析到细分市场数据，请确认会员额度或在网页端验证同条件查询结果。"

        return MarketResearchResponse(
            marketplace=station, page=page, size=size,
            returned=len(items), has_more=len(items) >= size,
            items=items, notice=notice,
        )
