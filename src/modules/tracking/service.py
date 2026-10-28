"""
常态化追踪看板服务层
------------------------------------------------
读取用户在卖家精灵网页端已经建立的产品/关键词/店铺监控看板。

说明：追踪看板的数据由卖家精灵后台按计划任务采集，本服务只做读取与结构化，
不主动创建监控任务（创建动作涉及扣减监控额度，应由用户在网页端确认后操作）。
"""
import re
import logging
from typing import List, Optional

from src.core.base_client import BaseClient
from src.core.parser import pick_table, to_number, to_int, find_col, cell
from src.schemas.tracking import (
    TrackedProductItem, TrackedProductResponse,
    TrackedKeywordItem, TrackedKeywordResponse,
    TrackedStoreItem, TrackedStoreResponse,
)

logger = logging.getLogger(__name__)

ASIN_RE = re.compile(r"\b(B0[A-Z0-9]{8})\b")
NO_DATA_HINT = (
    "未读取到监控数据。追踪看板只读取您在卖家精灵网页端已建立的监控对象，"
    "请先在网页端「产品监控 / 关键词监控 / 店铺监控」中添加目标后重试。"
)
WRONG_TABLE_HINT = (
    "页面返回的表头与预期模块不一致（已拒绝解析，避免给出错位数据）。"
    "常见原因：该 URL 被服务端重定向到其他监控模块，或官网改版。"
    "请先在浏览器人工确认该页面能正常打开。"
)


def _has_any_col(headers: List[str], *aliases: str) -> bool:
    """表头健全性校验：确认解析到的确实是目标模块的表，防止字段错位"""
    return any(any(a in h for h in headers) for a in aliases)


class TrackingService(BaseClient):
    PRODUCT_URL = "https://www.sellersprite.com/v2/product-tracking"
    KEYWORD_URL = "https://www.sellersprite.com/v2/keyword-tracking"
    STORE_URL = "https://www.sellersprite.com/v2/store-tracking"

    def _load_page(self, url: str, params: Optional[dict] = None) -> str:
        resp = self.get(url, params=params or {}, timeout=120, headers={"Referer": url})
        return resp.text

    # ==================== 4.1 产品监控 ====================

    def products(self, marketplace: str = "US", tag: Optional[str] = None,
                 page: int = 1, size: int = 50) -> TrackedProductResponse:
        html = self._load_page(self.PRODUCT_URL, {
            "station": marketplace.upper(), "marketId": "1",
            "page": page, "size": size,
            **({"tag": tag} if tag else {}),
        })
        table = pick_table(html, prefer_class="js-freeze-header", min_rows=1)

        items: List[TrackedProductItem] = []
        notice = None
        if table:
            headers = table["headers"]
            # 产品监控表必须含商品维度列；否则说明拿到的是别的模块的表（如关键词监控）
            if not _has_any_col(headers, "商品信息", "标题", "ASIN"):
                logger.warning(f"[产品监控] 表头不符合预期，已拒绝解析: {headers[:6]}")
                return TrackedProductResponse(
                    marketplace=marketplace.upper(), tag=tag,
                    total=0, returned=0, items=[], notice=WRONG_TABLE_HINT,
                )
            c_title = find_col(headers, "商品信息", "标题")
            c_price = find_col(headers, "价格")
            c_bsr = find_col(headers, "BSR")
            c_sales = find_col(headers, "月销量")
            c_rating = find_col(headers, "评分", "星级")
            c_reviews = find_col(headers, "评分数", "评论数")
            c_tag = find_col(headers, "标签")
            c_time = find_col(headers, "更新", "时间")

            for row in table["rows"]:
                joined = " ".join(row)
                m = ASIN_RE.search(joined)
                if not m:
                    continue
                items.append(TrackedProductItem(
                    asin=m.group(1),
                    title=cell(row, c_title),
                    tag=cell(row, c_tag) or tag,
                    current_price=to_number(cell(row, c_price)),
                    bsr_rank=to_int(cell(row, c_bsr)),
                    monthly_sales=to_int(cell(row, c_sales)),
                    rating=to_number(cell(row, c_rating)),
                    ratings_count=to_int(cell(row, c_reviews)),
                    last_updated=cell(row, c_time),
                ))

        return TrackedProductResponse(
            marketplace=marketplace.upper(), tag=tag,
            total=len(items), returned=len(items),
            items=items, notice=notice or (None if items else NO_DATA_HINT),
        )

    # ==================== 4.2 关键词排名监控 ====================

    def keywords(self, marketplace: str = "US", tag: Optional[str] = None,
                 page: int = 1, size: int = 50) -> TrackedKeywordResponse:
        html = self._load_page(self.KEYWORD_URL, {
            "station": marketplace.upper(), "marketId": "1",
            "page": page, "size": size,
            **({"tag": tag} if tag else {}),
        })
        table = pick_table(html, prefer_class="js-freeze-header", min_rows=1)

        items: List[TrackedKeywordItem] = []
        if table:
            headers = table["headers"]
            if not _has_any_col(headers, "关键词"):
                logger.warning(f"[关键词监控] 表头不符合预期，已拒绝解析: {headers[:6]}")
                return TrackedKeywordResponse(
                    marketplace=marketplace.upper(), tag=tag,
                    total=0, returned=0, items=[], notice=WRONG_TABLE_HINT,
                )
            c_kw = find_col(headers, "关键词")
            c_organic = find_col(headers, "自然", "organic")
            c_sponsored = find_col(headers, "广告", "sponsor")
            c_best = find_col(headers, "最佳", "历史")
            c_tag = find_col(headers, "标签")
            c_time = find_col(headers, "更新", "时间")

            for row in table["rows"]:
                kw = cell(row, c_kw)
                if not kw or not re.search(r"[A-Za-z]", kw):
                    continue
                joined = " ".join(row)
                m = ASIN_RE.search(joined)
                items.append(TrackedKeywordItem(
                    keyword=kw.split("\n")[0].strip(),
                    asin=m.group(1) if m else None,
                    tag=cell(row, c_tag) or tag,
                    current_organic_rank=to_int(cell(row, c_organic)),
                    current_sponsored_rank=to_int(cell(row, c_sponsored)),
                    best_organic_rank=to_int(cell(row, c_best)),
                    last_updated=cell(row, c_time),
                ))

        return TrackedKeywordResponse(
            marketplace=marketplace.upper(), tag=tag,
            total=len(items), returned=len(items),
            items=items, notice=None if items else NO_DATA_HINT,
        )

    # ==================== 4.3 店铺 / 竞店监控 ====================

    def stores(self, marketplace: str = "US", tag: Optional[str] = None,
               page: int = 1, size: int = 50) -> TrackedStoreResponse:
        html = self._load_page(self.STORE_URL, {
            "station": marketplace.upper(), "marketId": "1",
            "page": page, "size": size,
        })
        table = pick_table(html, prefer_class="js-freeze-header", min_rows=1)

        items: List[TrackedStoreItem] = []
        if table:
            headers = table["headers"]
            # 店铺监控表必须含店铺/卖家维度列；官网该页有时返回无表头的空壳
            if not _has_any_col(headers, "店铺", "卖家", "品牌"):
                logger.warning(f"[店铺监控] 表头不符合预期，已拒绝解析: {headers[:6]}")
                return TrackedStoreResponse(
                    marketplace=marketplace.upper(),
                    total=0, returned=0, items=[], notice=WRONG_TABLE_HINT,
                )
            c_name = find_col(headers, "店铺", "卖家")
            c_count = find_col(headers, "商品数", "商品数量")
            c_new = find_col(headers, "新增", "上新")
            c_tag = find_col(headers, "标签")
            c_time = find_col(headers, "更新", "时间")
            nodes = table.get("nodes") or []

            for idx, row in enumerate(table["rows"]):
                name = cell(row, c_name)
                url = None
                if idx < len(nodes):
                    a = nodes[idx].find("a", href=re.compile(r"/stores/|/seller/"))
                    if a:
                        url = a.get("href")
                        name = name or a.get_text(strip=True)
                if not name:
                    continue
                items.append(TrackedStoreItem(
                    store_name=name,
                    store_url=url,
                    product_count=to_int(cell(row, c_count)),
                    new_product_count=to_int(cell(row, c_new)),
                    tag=cell(row, c_tag) or tag,
                    last_updated=cell(row, c_time),
                ))

        return TrackedStoreResponse(
            marketplace=marketplace.upper(),
            total=len(items), returned=len(items),
            items=items, notice=None if items else NO_DATA_HINT,
        )
