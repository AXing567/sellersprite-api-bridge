from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 任务 2.1 关键词挖掘（选词） ============

class KeywordResearchItem(BaseModel):
    rank: Optional[int] = Field(None, description="当前排序下的序号")
    keyword: str = Field(..., description="关键词（英文原词）")
    keyword_cn: Optional[str] = Field(None, description="关键词中文翻译")
    monthly_search_volume: Optional[int] = Field(None, description="月搜索量")
    daily_search_volume: Optional[int] = Field(None, description="日均搜索量（月搜索量/30）")
    monthly_purchases: Optional[int] = Field(None, description="月购买量")
    purchase_rate: Optional[float] = Field(None, description="购买率 0~1")
    impressions: Optional[int] = Field(None, description="月展示量")
    clicks: Optional[int] = Field(None, description="月点击量")
    growth_rate: Optional[float] = Field(None, description="月环比增长率 0~1")
    yoy_growth_rate: Optional[float] = Field(None, description="同比增长率 0~1")
    click_concentration: Optional[float] = Field(None, description="点击集中度（头部商品垄断度）0~1")
    aba_rank: Optional[int] = Field(None, description="ABA 搜索频率排名")
    traffic_value: Optional[float] = Field(None, description="货流值（关键词引流成本指数）")
    ppc_bid: Optional[float] = Field(None, description="PPC 建议竞价")
    ppc_bid_low: Optional[float] = Field(None, description="PPC 竞价区间下限")
    ppc_bid_high: Optional[float] = Field(None, description="PPC 竞价区间上限")
    supply_demand_ratio: Optional[float] = Field(None, description="需供比（月搜索量 / 在售商品数）")
    product_count: Optional[int] = Field(None, description="该关键词下的在售商品数")
    market_avg_price: Optional[float] = Field(None, description="搜索结果 Top 商品平均价格")
    market_monthly_sales: Optional[int] = Field(None, description="搜索结果 Top 商品月总销量")
    market_avg_rating: Optional[float] = Field(None, description="搜索结果 Top 商品平均评分")
    sample_product_title: Optional[str] = Field(None, description="示例展示产品标题")


class KeywordResearchResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    keyword: Optional[str] = Field(None, description="本次查询的关键词条件")
    page: int = Field(1, description="当前页码")
    size: int = Field(20, description="每页条数")
    returned: int = Field(0, description="本次返回条数")
    has_more: bool = Field(False, description="是否还有下一页")
    items: List[KeywordResearchItem] = Field(default_factory=list, description="关键词明细列表")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")


# ============ 任务 2.2 出单词反查 / ABA ============

class AbaReverseItem(BaseModel):
    keyword: str = Field(..., description="出单关键词")
    search_frequency_rank: Optional[int] = Field(None, description="ABA 搜索频率排名")
    click_share: Optional[float] = Field(None, description="点击份额 0~1")
    conversion_share: Optional[float] = Field(None, description="转化份额 0~1")
    search_volume: Optional[int] = Field(None, description="月搜索量")
    organic_rank: Optional[int] = Field(None, description="该 ASIN 的自然排名")
    sponsored_rank: Optional[int] = Field(None, description="该 ASIN 的广告排名")


class AbaReverseResponse(BaseModel):
    asin: str = Field(..., description="查询的 ASIN")
    marketplace: str = Field("US", description="站点代码")
    table_period: Optional[str] = Field(None, description="数据周期标识（如 ara_20261017 表示该周 ABA 表）")
    total: int = Field(0, description="出单词总数")
    returned: int = Field(0, description="本次返回条数")
    items: List[AbaReverseItem] = Field(default_factory=list, description="出单词明细")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")


# ============ 任务 2.2b 关键词反查（ASIN -> 全量关键词） ============

class KeywordReverseItem(BaseModel):
    keyword: str = Field(..., description="关键词")
    keyword_cn: Optional[str] = Field(None, description="关键词中文翻译")
    search_rank: Optional[int] = Field(None, description="ABA 搜索频率排名（数值越小越热门）")
    searches: Optional[int] = Field(None, description="月搜索量")
    clicks: Optional[int] = Field(None, description="月点击量")
    impressions: Optional[int] = Field(None, description="月展示量")
    click_share: Optional[float] = Field(None, description="该 ASIN 在此词下的点击份额 0~1")
    conversion_share: Optional[float] = Field(None, description="该 ASIN 在此词下的转化份额 0~1")
    purchase_rate: Optional[float] = Field(None, description="购买率 0~1")
    purchases: Optional[int] = Field(None, description="月购买量")
    organic_rank: Optional[int] = Field(None, description="该 ASIN 自然排名位次（若数据源提供）")
    sponsored_rank: Optional[int] = Field(None, description="该 ASIN 广告排名位次（若数据源提供）")


class KeywordReverseResponse(BaseModel):
    asin: str = Field(..., description="查询的 ASIN")
    marketplace: str = Field("US", description="站点代码")
    source: str = Field("keyword-reverse",
                        description="数据来源：keyword-reverse（网页版关键词反查主通道）"
                                    " / aba-reverse（ABA 出单词反查降级通道）")
    period: Optional[str] = Field(None, description="数据周期（ABA 通道时为表名，如 ara_20261017）")
    total: int = Field(0, description="该 ASIN 的关键词总数")
    returned: int = Field(0, description="本次返回条数")
    items: List[KeywordReverseItem] = Field(default_factory=list, description="关键词明细")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")


# ============ 任务 2.3 关键词收录检测 ============

class KeywordCheckerItem(BaseModel):
    keyword: str = Field(..., description="被检测的关键词")
    is_indexed: bool = Field(False, description="是否被该 ASIN 收录（有曝光/有排名）")
    is_organic_indexed: bool = Field(False, description="是否自然位收录")
    organic_rank: Optional[int] = Field(None, description="自然排名位置，未收录为 None")
    is_sponsored_indexed: bool = Field(False, description="是否广告位收录")
    sponsored_rank: Optional[int] = Field(None, description="广告排名位置，未收录为 None")
    page_no: Optional[int] = Field(None, description="出现在搜索结果第几页")
    evidence: Optional[str] = Field(None, description="判定依据（命中的原始关键词 / 数据缺口说明）")


class KeywordCheckerResponse(BaseModel):
    asin: str = Field(..., description="检测的 ASIN")
    marketplace: str = Field("US", description="站点代码")
    source: Optional[str] = Field(None, description="本次判定所用的数据来源")
    checked: int = Field(0, description="实际检测的关键词数")
    indexed_count: int = Field(0, description="已收录关键词数")
    items: List[KeywordCheckerItem] = Field(default_factory=list, description="逐个关键词的收录结果")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")
