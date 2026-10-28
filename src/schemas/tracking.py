from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TrackedProductItem(BaseModel):
    asin: str = Field(..., description="被监控的 ASIN")
    title: Optional[str] = Field(None, description="商品标题")
    image_url: Optional[str] = Field(None, description="主图")
    tag: Optional[str] = Field(None, description="自定义标签/分组")
    current_price: Optional[float] = Field(None, description="最新价格")
    bsr_rank: Optional[int] = Field(None, description="最新 BSR")
    monthly_sales: Optional[int] = Field(None, description="最新月销量")
    rating: Optional[float] = Field(None, description="评分")
    ratings_count: Optional[int] = Field(None, description="评分数")
    last_updated: Optional[str] = Field(None, description="最近更新时间")


class TrackedProductResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    tag: Optional[str] = Field(None, description="查询的标签/分组")
    total: int = Field(0, description="监控商品总数")
    returned: int = Field(0, description="本次返回条数")
    items: List[TrackedProductItem] = Field(default_factory=list, description="监控商品列表")
    notice: Optional[str] = Field(None, description="数据获取说明")


class TrackedKeywordItem(BaseModel):
    keyword: str = Field(..., description="被监控的关键词")
    asin: Optional[str] = Field(None, description="关联 ASIN")
    tag: Optional[str] = Field(None, description="标签/分组")
    current_organic_rank: Optional[int] = Field(None, description="当前自然排名")
    current_sponsored_rank: Optional[int] = Field(None, description="当前广告排名")
    best_organic_rank: Optional[int] = Field(None, description="历史最佳自然排名")
    last_updated: Optional[str] = Field(None, description="最近更新时间")


class TrackedKeywordResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    tag: Optional[str] = Field(None, description="查询的标签/分组")
    total: int = Field(0, description="监控词总数")
    returned: int = Field(0, description="本次返回条数")
    items: List[TrackedKeywordItem] = Field(default_factory=list, description="监控关键词列表")
    notice: Optional[str] = Field(None, description="数据获取说明")


class TrackedStoreItem(BaseModel):
    store_name: Optional[str] = Field(None, description="店铺名称")
    store_url: Optional[str] = Field(None, description="店铺链接")
    seller_id: Optional[str] = Field(None, description="卖家/店铺 ID")
    product_count: Optional[int] = Field(None, description="在售商品数")
    new_product_count: Optional[int] = Field(None, description="近期新增商品数")
    tag: Optional[str] = Field(None, description="标签/分组")
    last_updated: Optional[str] = Field(None, description="最近更新时间")


class TrackedStoreResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    total: int = Field(0, description="监控店铺总数")
    returned: int = Field(0, description="本次返回条数")
    items: List[TrackedStoreItem] = Field(default_factory=list, description="监控店铺列表")
    notice: Optional[str] = Field(None, description="数据获取说明")
