from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# ============ 任务 3.1 产品库多维度选品 ============

class ProductItem(BaseModel):
    rank: Optional[int] = Field(None, description="当前排序序号")
    asin: Optional[str] = Field(None, description="商品 ASIN")
    parent_asin: Optional[str] = Field(None, description="父体 ASIN")
    title: Optional[str] = Field(None, description="商品标题")
    image_url: Optional[str] = Field(None, description="主图链接")
    brand: Optional[str] = Field(None, description="品牌")
    category: Optional[str] = Field(None, description="所属类目")
    badges: Optional[List[str]] = Field(None, description="商品徽章，如 A+(A+页面) / V(视频) / BS(Best Seller) / AC(Amazon's Choice)")

    price: Optional[float] = Field(None, description="当前售价")
    qa_count: Optional[int] = Field(None, description="Q&A 问答数")
    bsr_rank: Optional[int] = Field(None, description="大类 BSR")
    bsr_growth: Optional[int] = Field(None, description="BSR 排名变化数（负数为上升）")
    bsr_growth_rate: Optional[float] = Field(None, description="BSR 排名变化率 0~1（负数为上升）")

    monthly_sales: Optional[int] = Field(None, description="近30天销量")
    sales_growth: Optional[float] = Field(None, description="销量增长率 0~1")
    monthly_revenue: Optional[float] = Field(None, description="近30天销售额")
    revenue_growth: Optional[float] = Field(None, description="销售额增长率 0~1")

    gross_margin: Optional[float] = Field(None, description="毛利率 0~1（选品核心指标）")
    fba_fee: Optional[float] = Field(None, description="FBA 运费（美元）")

    rating: Optional[float] = Field(None, description="评分星级")
    rating_monthly_new: Optional[int] = Field(None, description="月新增评分数")
    ratings_count: Optional[int] = Field(None, description="累计评分数")
    review_rate: Optional[float] = Field(None, description="留评率 0~1")

    release_date: Optional[str] = Field(None, description="上架日期 YYYY-MM-DD")
    listing_age: Optional[str] = Field(None, description="上架时长，如 5年9个月")

    seller_type: Optional[str] = Field(None, description="发货方式：AMZ(亚马逊自营) / FBA / FBM")
    buyer_shipping_fee: Optional[float] = Field(None, description="买家运费（美元）")
    variation_count: Optional[int] = Field(None, description="变体数")


class ProductFilterResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    month_name: str = Field("bsr_sales_nearly", description="统计月份：bsr_sales_nearly(近30天) 或 具体月份 bsr_sales_monthly_YYYYMM")
    order_field: str = Field("total_units", description="实际生效的排序字段")
    page: int = Field(1, description="页码")
    size: int = Field(20, description="每页条数")
    returned: int = Field(0, description="返回条数")
    has_more: bool = Field(False, description="是否还有下一页")
    items: List[ProductItem] = Field(default_factory=list, description="商品明细")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")


# ============ 任务 3.2 细分市场分析 ============

class MarketItem(BaseModel):
    rank: Optional[int] = Field(None, description="序号")
    market_name: Optional[str] = Field(None, description="细分市场名称")
    market_path: Optional[str] = Field(None, description="完整类目路径")
    sample_product_count: Optional[int] = Field(None, description="样本商品数")
    brand_count: Optional[int] = Field(None, description="涉及品牌数")
    seller_count: Optional[int] = Field(None, description="涉及卖家数")

    monthly_sales_total: Optional[int] = Field(None, description="月总销量")
    monthly_sales_avg: Optional[int] = Field(None, description="月均销量")
    monthly_sales_avg_top: Optional[int] = Field(None, description="头部商品月均销量")
    monthly_revenue_avg: Optional[float] = Field(None, description="月均销售额")
    monthly_revenue_avg_top: Optional[float] = Field(None, description="头部商品月均销售额")

    avg_ratings_count: Optional[int] = Field(None, description="平均评分数")
    avg_rating: Optional[float] = Field(None, description="平均星级")
    avg_bsr: Optional[int] = Field(None, description="平均 BSR")
    avg_bsr_top: Optional[int] = Field(None, description="头部商品平均 BSR")

    avg_seller_num: Optional[float] = Field(None, description="平均跟卖卖家数")
    avg_price: Optional[float] = Field(None, description="平均价格")

    fba_ratio: Optional[float] = Field(None, description="FBA 卖家占比 0~1")
    amz_ratio: Optional[float] = Field(None, description="亚马逊自营占比 0~1")
    fbm_ratio: Optional[float] = Field(None, description="FBM 卖家占比 0~1")

    product_monopoly_ratio: Optional[float] = Field(None, description="商品集中度（头部商品销量占比）0~1")
    brand_monopoly_ratio: Optional[float] = Field(None, description="品牌集中度 0~1")
    seller_monopoly_ratio: Optional[float] = Field(None, description="卖家集中度 0~1")

    new_product_count: Optional[int] = Field(None, description="新品数量")
    new_product_ratio: Optional[float] = Field(None, description="新品占比 0~1")
    total_product_count: Optional[int] = Field(None, description="市场商品总数")
    return_rate: Optional[float] = Field(None, description="退货率 0~1")
    category_avg_return_rate: Optional[float] = Field(None, description="同类目平均退货率 0~1")
    node_id: Optional[str] = Field(None, description="类目节点 ID")
    node_id_path: Optional[str] = Field(None, description="类目节点完整路径（可直接传给 /product/filter 的 node_id_path）")

    # ---------- 类目深度指标（来自市场路径展开行）----------
    market_path_cn: Optional[str] = Field(None, description="完整类目路径（中文）")
    aplus_ratio: Optional[float] = Field(None, description="A+ 页面数量占比 0~1")
    new_avg_ratings: Optional[int] = Field(None, description="新品平均评分数")
    new_avg_price: Optional[float] = Field(None, description="新品平均价格")
    new_avg_rating: Optional[float] = Field(None, description="新品平均星级")
    new_avg_sales: Optional[int] = Field(None, description="新品月均销量")
    new_avg_revenue: Optional[float] = Field(None, description="新品月均销售额")
    avg_weight_pounds: Optional[float] = Field(None, description="平均重量（磅）")
    avg_volume_inch3: Optional[float] = Field(None, description="平均体积（立方英寸）")
    avg_gross_margin: Optional[float] = Field(None, description="平均毛利率 0~1（选品核心指标）")
    china_seller_ratio: Optional[float] = Field(None, description="中国卖家占比 0~1")
    search_purchase_ratio: Optional[str] = Field(None, description="搜索购买比，如 11.8‰")


class MarketResearchResponse(BaseModel):
    marketplace: str = Field("US", description="站点代码")
    page: int = Field(1, description="页码")
    size: int = Field(20, description="每页条数")
    returned: int = Field(0, description="返回条数")
    has_more: bool = Field(False, description="是否还有下一页")
    items: List[MarketItem] = Field(default_factory=list, description="细分市场列表")
    notice: Optional[str] = Field(None, description="数据获取说明/降级提示")
