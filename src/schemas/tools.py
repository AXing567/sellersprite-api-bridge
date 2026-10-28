from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 任务 5.2 FBA 利润计算器 ============

class ProfitCalculatorRequest(BaseModel):
    selling_price: float = Field(..., description="售价（当地货币）")
    product_cost: float = Field(..., description="采购成本（含税单价）")
    referral_rate: Optional[float] = Field(0.15, description="亚马逊佣金率，默认 15%")
    referral_min_fee: Optional[float] = Field(0.30, description="佣金最低收取额，美国站默认 0.30")
    fba_fulfillment_fee: Optional[float] = Field(None, description="FBA 配送费；不填则按重量自动估算")
    shipping_weight_pounds: Optional[float] = Field(1.0, description="计费重量（磅），用于自动估算 FBA 配送费")
    first_leg_shipping: Optional[float] = Field(0.0, description="头程物流分摊到单件的成本")
    monthly_storage_fee: Optional[float] = Field(0.0, description="月仓储费分摊到单件")
    advertising_rate: Optional[float] = Field(0.0, description="广告费占售价比，如 0.10 表示 ACoS 10%")
    return_rate: Optional[float] = Field(0.0, description="退货率 0~1，用于摊算退货损耗")
    return_loss_per_unit: Optional[float] = Field(0.0, description="单件退货的实际损失（不可售+运费）")
    other_cost: Optional[float] = Field(0.0, description="其它成本（包装、贴标等）")


class ProfitCalculatorResponse(BaseModel):
    selling_price: float = Field(..., description="售价")
    referral_fee: float = Field(..., description="亚马逊佣金")
    fba_fulfillment_fee: float = Field(..., description="FBA 配送费")
    first_leg_shipping: float = Field(..., description="头程物流")
    monthly_storage_fee: float = Field(..., description="月仓储费")
    advertising_fee: float = Field(..., description="广告费")
    expected_return_loss: float = Field(..., description="退货损耗摊算")
    product_cost: float = Field(..., description="采购成本")
    other_cost: float = Field(..., description="其它成本")

    total_cost: float = Field(..., description="总成本合计")
    net_profit: float = Field(..., description="单件净利润")
    net_margin: float = Field(..., description="净利率 0~1")
    gross_profit: float = Field(..., description="毛利（售价 - 佣金 - FBA费 - 采购成本）")
    gross_margin: float = Field(..., description="毛利率 0~1")
    roi: float = Field(..., description="投入产出比 = 净利润 / 总成本")
    break_even_price: float = Field(..., description="保本售价（净利润为 0 的售价）")


# ============ 任务 5.1 BSR 销量预测 ============

class SalesEstimatorResponse(BaseModel):
    asin: Optional[str] = Field(None, description="商品 ASIN")
    marketplace: str = Field("US", description="站点代码")
    bsr_rank: Optional[int] = Field(None, description="输入的 BSR 排名")
    category: Optional[str] = Field(None, description="所属类目名称")
    est_monthly_sales: int = Field(0, description="预估月销量（件）")
    est_daily_sales: int = Field(0, description="预估日均销量（件）")
    est_monthly_revenue: Optional[float] = Field(None, description="预估月销售额（需提供售价）")
    confidence: str = Field("low", description="置信度: high / medium / low")
    method: str = Field("", description="估算方法说明")
    notice: Optional[str] = Field(None, description="使用限制说明")
