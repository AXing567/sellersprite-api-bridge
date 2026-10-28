import re
import time
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.core.session_manager import SellerSpriteSession
from src.schemas.competitor import (
    CompetitorCoreInfoSchema,
    CompetitorSalesRankSchema,
    CompetitorPromotionSchema,
    CompetitorReviewsSchema,
    CompetitorTrafficKeywordsSchema,
    CompetitorAggregatedMonitorSchema,
    KeywordRankItem,
)

logger = logging.getLogger(__name__)

MARKETPLACE_TO_ID = {
    "US": "1",
    "JP": "2",
    "UK": "3",
    "DE": "4",
    "FR": "5",
    "IT": "6",
    "ES": "7",
    "CA": "8",
    "IN": "9"
}

class CompetitorService:
    """
    竞品监控服务：
    拆分为原子能力获取与顶层聚合能力
    """
    LOOKUP_URL = "https://www.sellersprite.com/v2/competitor-lookup/monthly"
    CACHE_TTL_SECONDS = 180  # 同一 ASIN 的反查页缓存 3 分钟，避免聚合接口重复拉取

    def __init__(self, session_manager: Optional[SellerSpriteSession] = None):
        self.session_mgr = session_manager or SellerSpriteSession()
        self._cache: Dict[str, Any] = {}

    def _fetch_lookup_html(self, asin: str, marketplace: str = "US") -> Optional[str]:
        market_id = MARKETPLACE_TO_ID.get(marketplace.upper(), "1")
        cache_key = f"{marketplace.upper()}:{asin.strip().upper()}"

        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached[0]) < self.CACHE_TTL_SECONDS:
            logger.debug(f"[缓存命中] competitor-lookup {cache_key}")
            return cached[1]

        payload = {
            "marketId": market_id,
            "station": marketplace.upper(),
            "competing": "true",
            "type": "monthly",
            "textareaValue": asin.strip(),
            "order.field": "total_units",
            "order.desc": "true"
        }

        resp = self.session_mgr.request("POST", self.LOOKUP_URL, data=payload, timeout=25)

        if resp.status_code != 200:
            logger.error(f"请求卖家精灵失败: {resp.status_code}")
            return None

        self._cache[cache_key] = (time.time(), resp.text)
        return resp.text

    def _find_row_tds(self, html: str, target_asin: str):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="js-freeze-header")
        if not table:
            return None
        tbody = table.find("tbody")
        if not tbody:
            return None
        rows = tbody.find_all("tr", recursive=False)
        for row in rows:
            tds = row.find_all("td", recursive=False)
            if len(tds) < 13:
                continue
            info_text = tds[2].get_text()
            if target_asin.upper() in info_text.upper():
                return tds
        return None

    # ==================== 原子接口实现 ====================

    def get_core_info(self, asin: str, marketplace: str = "US") -> Optional[CompetitorCoreInfoSchema]:
        """原子接口 1: 获取核心画像与状态"""
        html = self._fetch_lookup_html(asin, marketplace)
        if not html:
            return None
        tds = self._find_row_tds(html, asin)
        if not tds:
            return None

        info_text = tds[2].get_text()

        # 标题
        title = ""
        h1_div = tds[2].find("div", class_="h-1")
        if h1_div:
            title = h1_div.get("title") or h1_div.get_text(strip=True)
        if not title:
            title_span = tds[2].find("span")
            title = title_span.get_text(strip=True) if title_span else asin.upper()

        # 主图
        img_url = None
        img_a = tds[1].find("a", class_="item-img-preset")
        if img_a:
            img_url = img_a.get("href")
        if not img_url:
            img_tag = tds[1].find("img") or tds[2].find("img")
            img_url = img_tag.get("src") or img_tag.get("data-src") if img_tag else None

        # 父体 PASIN
        parent_match = re.search(r'PASIN:\s*([A-Z0-9]{10})', info_text)
        parent_asin = parent_match.group(1) if parent_match else None

        # 品牌
        brand = None
        brand_url = None
        for a in tds[2].find_all("a"):
            href = a.get("href", "")
            if "/stores/" in href or "brand" in a.get("class", []):
                brand = a.get_text(strip=True)
                brand_url = href
                break

        # 价格
        price_tokens = tds[7].get_text().split()
        price_raw = price_tokens[0].replace("$", "").replace("¥", "").replace("€", "").replace(",", "") if price_tokens else ""
        try:
            current_price = float(price_raw) if price_raw else None
        except ValueError:
            current_price = None

        # 上架时间
        date_tokens = tds[11].get_text().split()
        release_date = date_tokens[0] if date_tokens and re.match(r'^\d{4}-\d{2}-\d{2}$', date_tokens[0]) else None

        # 配送方式
        shipping_tokens = tds[12].get_text().split()
        fulfillment_type = shipping_tokens[0] if shipping_tokens else "FBA"

        return CompetitorCoreInfoSchema(
            asin=asin.upper(),
            parent_asin=parent_asin,
            marketplace=marketplace.upper(),
            title=title,
            brand=brand,
            brand_url=brand_url,
            image_url=img_url,
            current_price=current_price,
            original_price=None,
            seller_name=None,
            fulfillment_type=fulfillment_type,
            stock_status="IN_STOCK",
            release_date=release_date,
            category_path=[]
        )

    def get_sales_rank(self, asin: str, marketplace: str = "US") -> Optional[CompetitorSalesRankSchema]:
        """原子接口 2: 获取销量与排名动向"""
        html = self._fetch_lookup_html(asin, marketplace)
        if not html:
            return None
        tds = self._find_row_tds(html, asin)
        if not tds:
            return None

        # BSR 排名
        bsr_tokens = tds[3].get_text().split()
        bsr_rank = int(bsr_tokens[0].replace(",", "")) if bsr_tokens and bsr_tokens[0].isdigit() else None

        # 销量
        sales_tokens = tds[5].get_text().split()
        sales_raw = sales_tokens[0].replace(",", "") if sales_tokens else ""
        est_sales = int(sales_raw) if sales_raw.isdigit() else None

        # 销售额
        rev_tokens = tds[6].get_text().split()
        rev_raw = rev_tokens[0].replace("$", "").replace("¥", "").replace("€", "").replace(",", "") if rev_tokens else ""
        try:
            est_revenue = float(rev_raw) if rev_raw else None
        except ValueError:
            est_revenue = None

        est_daily = int(est_sales / 30) if est_sales else None

        return CompetitorSalesRankSchema(
            asin=asin.upper(),
            marketplace=marketplace.upper(),
            bsr_main_rank=bsr_rank,
            bsr_main_category=None,
            bsr_sub_rank=None,
            bsr_sub_category=None,
            est_monthly_sales=est_sales,
            est_monthly_revenue=est_revenue,
            est_daily_sales=est_daily
        )

    def get_promotions(self, asin: str, marketplace: str = "US") -> Optional[CompetitorPromotionSchema]:
        """原子接口 3: 获取促销与优惠券动向"""
        html = self._fetch_lookup_html(asin, marketplace)
        if not html:
            return None
        tds = self._find_row_tds(html, asin)
        if not tds:
            return None

        # 标价
        price_tokens = tds[7].get_text().split()
        price_raw = price_tokens[0].replace("$", "").replace("¥", "").replace("€", "").replace(",", "") if price_tokens else ""
        try:
            current_price = float(price_raw) if price_raw else None
        except ValueError:
            current_price = None

        return CompetitorPromotionSchema(
            asin=asin.upper(),
            marketplace=marketplace.upper(),
            current_price=current_price,
            coupon_value=None,
            coupon_type=None,
            deal_type=None,
            net_price=current_price
        )

    def get_reviews(self, asin: str, marketplace: str = "US") -> Optional[CompetitorReviewsSchema]:
        """原子接口 4: 获取口碑与评价监控"""
        html = self._fetch_lookup_html(asin, marketplace)
        if not html:
            return None
        tds = self._find_row_tds(html, asin)
        if not tds:
            return None

        # 评论总数
        reviews_tokens = tds[9].get_text().split()
        rev_raw = reviews_tokens[0].replace(",", "") if reviews_tokens else ""
        ratings_count = int(rev_raw) if rev_raw.isdigit() else None

        # 评分星级
        rating_tokens = tds[10].get_text().split()
        try:
            rating = float(rating_tokens[0]) if rating_tokens else None
        except ValueError:
            rating = None

        # 月新增评分
        monthly_inc = int(rating_tokens[1].replace(",", "")) if len(rating_tokens) > 1 and rating_tokens[1].isdigit() else None

        return CompetitorReviewsSchema(
            asin=asin.upper(),
            marketplace=marketplace.upper(),
            rating=rating,
            ratings_count=ratings_count,
            monthly_ratings_increment=monthly_inc,
            rating_breakdown={}
        )

    def get_traffic_keywords(self, asin: str, marketplace: str = "US",
                             limit: int = 20) -> Optional[CompetitorTrafficKeywordsSchema]:
        """
        原子接口 5: 获取流量结构与关键词

        数据源策略（双通道冗余）：
          主通道 /v2/keyword-reverse  —— 官网「关键词反查」，含自然位/广告位排名
          备通道 /v2/aba/reverse/search/more —— 官网「出单词反查」，含点击份额/转化份额
        主通道返回空时自动切备通道，保证接口尽量有真实数据可用。
        """
        station = marketplace.upper()
        asin_u = asin.strip().upper()

        # ---------- 主通道：关键词反查 ----------
        url = f"https://www.sellersprite.com/v2/keyword-reverse/{station}/{asin_u}/more"
        resp = self.session_mgr.request(
            "GET", url, params={"pageNum": 1, "v": "false"}, timeout=120,
            headers={
                "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/{station}/{asin_u}",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

        items: List[KeywordRankItem] = []
        total = None
        notice = None
        source = "keyword-reverse"

        try:
            payload = resp.json()
            dto = payload.get("dto") or payload.get("data") or {}
            raw_items = dto.get("items") or []
            total = dto.get("total")
        except Exception:
            raw_items = []

        organic_cnt = 0
        sponsored_cnt = 0
        for it in raw_items[:limit]:
            kw = (it.get("keywords") or it.get("keyword") or "").strip()
            if not kw:
                continue
            organic_rank = it.get("organicRank") or it.get("rankOrganic") or it.get("naturalRank")
            sponsored_rank = it.get("adRank") or it.get("rankSponsored") or it.get("sponsoredRank")
            if organic_rank:
                organic_cnt += 1
            if sponsored_rank:
                sponsored_cnt += 1

            items.append(KeywordRankItem(
                keyword=kw,
                keyword_cn=it.get("keywordCn"),
                search_volume=int(it.get("searches") or 0),
                organic_rank=int(organic_rank) if organic_rank else None,
                sponsored_rank=int(sponsored_rank) if sponsored_rank else None,
                traffic_share=(float(it["hot"]) / 100.0) if it.get("hot") else None,
            ))

        # ---------- 备通道：ABA 出单词反查 ----------
        if not items:
            logger.info(f"[流量词] 主通道关键词反查为空，切换 ABA 出单词通道 (asin={asin_u})")
            try:
                from src.modules.keywords.service import KeywordService
                aba = KeywordService(self.session_mgr).aba_reverse(asin=asin_u, marketplace=station)
                if aba.items:
                    source = "aba-reverse"
                    total = aba.total
                    for it in aba.items[:limit]:
                        kw = (it.keyword or "").strip()
                        if not kw:
                            continue
                        if len(kw) > 120:  # ABA 有时把商品标题当搜索词，过长则截断
                            kw = kw[:120].rstrip() + "..."
                        items.append(KeywordRankItem(
                            keyword=kw,
                            search_volume=it.search_volume or 0,
                            traffic_share=it.click_share,
                        ))
                    notice = (
                        f"主通道「关键词反查」返回空结果（试用/免费账号通常不含该模块权益），"
                        f"已自动降级为「ABA 出单词反查」通道（周期 {aba.table_period}）。"
                        "ABA 通道不含自然位/广告位排名，但提供点击份额与转化份额，"
                        "可用于判断哪些词真正为竞品带来成交。"
                    )
            except Exception as e:
                logger.warning(f"[流量词] ABA 备通道也失败: {e}")

        if not items:
            notice = (
                "两个通道均未取到流量词数据。已在网页端确认该账号「关键词反查」可用后重试；"
                "若网页端也无数据，说明该 ASIN 尚无词库收录。"
            )

        return CompetitorTrafficKeywordsSchema(
            asin=asin_u,
            marketplace=station,
            traffic_keywords_total=int(total) if total else (len(items) or None),
            organic_traffic_ratio=round(organic_cnt / len(items), 4) if items and organic_cnt else None,
            sponsored_traffic_ratio=round(sponsored_cnt / len(items), 4) if items and sponsored_cnt else None,
            keywords_list=items,
            source=source,
            notice=notice,
        )

    # ==================== 顶层聚合接口 ====================

    def get_aggregated_monitor(self, asin: str, marketplace: str = "US") -> Optional[CompetitorAggregatedMonitorSchema]:
        """顶层聚合接口：聚合各个独立模块"""
        core = self.get_core_info(asin, marketplace)
        sales = self.get_sales_rank(asin, marketplace)
        promo = self.get_promotions(asin, marketplace)
        rev = self.get_reviews(asin, marketplace)
        traffic = self.get_traffic_keywords(asin, marketplace)

        if not core and not sales and not rev:
            return None

        return CompetitorAggregatedMonitorSchema(
            asin=asin.upper(),
            marketplace=marketplace.upper(),
            core_info=core,
            sales_rank=sales,
            promotions=promo,
            reviews=rev,
            traffic=traffic
        )
