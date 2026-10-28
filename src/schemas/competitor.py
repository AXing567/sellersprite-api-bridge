from typing import Optional, List, Dict
from pydantic import BaseModel, Field

# 1. 核心画像与基础状态
class CompetitorCoreInfoSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    parent_asin: Optional[str] = Field(None, description="父体 ASIN")
    marketplace: str = Field("US", description="站点代码")
    title: Optional[str] = Field(None, description="Listing 标题")
    brand: Optional[str] = Field(None, description="品牌名称")
    brand_url: Optional[str] = Field(None, description="品牌链接")
    image_url: Optional[str] = Field(None, description="主图高清链接")
    current_price: Optional[float] = Field(None, description="当前展示价 / BuyBox 价格")
    original_price: Optional[float] = Field(None, description="划线原价")
    seller_name: Optional[str] = Field(None, description="当前获得 BuyBox 的卖家")
    fulfillment_type: Optional[str] = Field(None, description="发货方式: FBA / FBM / AMZ自营")
    stock_status: Optional[str] = Field("IN_STOCK", description="库存状态: IN_STOCK / LOW_STOCK / OOS")
    release_date: Optional[str] = Field(None, description="上架时间 YYYY-MM-DD")
    category_path: List[str] = Field(default_factory=list, description="类目路径")

# 2. 销售与排名动向
class CompetitorSalesRankSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    bsr_main_rank: Optional[int] = Field(None, description="大类实时 BSR 排名")
    bsr_main_category: Optional[str] = Field(None, description="大类类目名称")
    bsr_sub_rank: Optional[int] = Field(None, description="核心小类实时排名")
    bsr_sub_category: Optional[str] = Field(None, description="小类节点名称")
    est_monthly_sales: Optional[int] = Field(None, description="预估月销量 (件)")
    est_monthly_revenue: Optional[float] = Field(None, description="预估月销售额 (当地货币)")
    est_daily_sales: Optional[int] = Field(None, description="预估日均销量")

# 3. 促销与优惠券动向
class CompetitorPromotionSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    current_price: Optional[float] = Field(None, description="标价")
    coupon_value: Optional[float] = Field(None, description="优惠券面额")
    coupon_type: Optional[str] = Field(None, description="优惠券类型: PERCENT / AMOUNT")
    deal_type: Optional[str] = Field(None, description="促销活动类型 (LD / 7DD / Prime专享等)")
    net_price: Optional[float] = Field(None, description="券后实际到手价")

# 4. 口碑与评价监控
class CompetitorReviewsSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    rating: Optional[float] = Field(None, description="评分星级 (如 4.3)")
    ratings_count: Optional[int] = Field(None, description="评论/Rating 总数")
    monthly_ratings_increment: Optional[int] = Field(None, description="近30天评分新增数")
    rating_breakdown: Optional[dict] = Field(default_factory=dict, description="各星级占比分布")

# 5. 流量结构与关键词
class KeywordRankItem(BaseModel):
    keyword: str = Field(..., description="关键词")
    keyword_cn: Optional[str] = Field(None, description="关键词中文翻译")
    search_volume: int = Field(0, description="月搜索量")
    organic_rank: Optional[int] = Field(None, description="自然排名位置")
    sponsored_rank: Optional[int] = Field(None, description="广告排名位置")
    traffic_share: Optional[float] = Field(None, description="该词为该ASIN贡献的流量占比 0~1")

class CompetitorTrafficKeywordsSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    traffic_keywords_total: Optional[int] = Field(None, description="总流量词数")
    organic_traffic_ratio: Optional[float] = Field(None, description="自然流量占比 (0.0~1.0)")
    sponsored_traffic_ratio: Optional[float] = Field(None, description="广告流量占比 (0.0~1.0)")
    keywords_list: List[KeywordRankItem] = Field(default_factory=list, description="核心流量词列表")
    source: Optional[str] = Field(None, description="数据来源通道: keyword-reverse(关键词反查) / aba-reverse(出单词反查)")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")

# 6. 最终的聚合总模型 (Facade 聚合响应)
class CompetitorAggregatedMonitorSchema(BaseModel):
    asin: str = Field(..., description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    core_info: Optional[CompetitorCoreInfoSchema] = Field(None, description="核心画像")
    sales_rank: Optional[CompetitorSalesRankSchema] = Field(None, description="销量与BSR")
    promotions: Optional[CompetitorPromotionSchema] = Field(None, description="促销优惠券")
    reviews: Optional[CompetitorReviewsSchema] = Field(None, description="评分与评价")
    traffic: Optional[CompetitorTrafficKeywordsSchema] = Field(None, description="流量与关键词")
