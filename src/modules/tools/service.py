"""
实用算法工具服务层
------------------------------------------------
  1. BSR 销量预测（本地估算模型，不依赖网页端，零额度消耗）
  2. FBA 利润计算器（完整费用拆解，纯本地计算）
"""
import logging
import math
from typing import Optional

from src.schemas.tools import (
    ProfitCalculatorRequest, ProfitCalculatorResponse,
    SalesEstimatorResponse,
)

logger = logging.getLogger(__name__)


# 美国站标准尺寸 FBA 配送费分档（磅 -> 费用，USD）
US_FBA_STANDARD_TIERS = [
    (0.25, 3.06),
    (0.50, 3.15),
    (0.75, 3.24),
    (1.00, 3.33),
    (1.25, 3.62),
    (1.50, 3.79),
    (1.75, 3.97),
    (2.00, 4.15),
    (2.50, 4.55),
    (3.00, 4.99),
]


def _estimate_fba_fee(weight_pounds: float) -> float:
    """按计费重量估算美国站 FBA 标准尺寸配送费"""
    if weight_pounds is None or weight_pounds <= 0:
        return US_FBA_STANDARD_TIERS[3][1]
    for limit, fee in US_FBA_STANDARD_TIERS:
        if weight_pounds <= limit:
            return fee
    # 超过 3 磅后按每磅加收近似
    return round(US_FBA_STANDARD_TIERS[-1][1] + (weight_pounds - 3.0) * 0.42, 2)


class ToolsService:
    """本地算法工具（不消耗卖家精灵额度）"""

    # ==================== 5.2 FBA 利润计算器 ====================

    def calc_profit(self, req: ProfitCalculatorRequest) -> ProfitCalculatorResponse:
        price = float(req.selling_price)
        referral_rate = req.referral_rate if req.referral_rate is not None else 0.15
        referral_fee = round(max(price * referral_rate, req.referral_min_fee or 0.30), 2)

        fba_fee = req.fba_fulfillment_fee
        if fba_fee is None:
            fba_fee = _estimate_fba_fee(req.shipping_weight_pounds or 1.0)
        fba_fee = round(float(fba_fee), 2)

        ad_fee = round(price * (req.advertising_rate or 0.0), 2)
        ret_loss = round((req.return_rate or 0.0) * (req.return_loss_per_unit or 0.0), 2)

        total_cost = round(
            referral_fee + fba_fee
            + (req.first_leg_shipping or 0.0)
            + (req.monthly_storage_fee or 0.0)
            + ad_fee + ret_loss
            + (req.product_cost or 0.0)
            + (req.other_cost or 0.0),
            2,
        )

        net_profit = round(price - total_cost, 2)
        net_margin = round(net_profit / price, 4) if price else 0.0
        gross_profit = round(price - referral_fee - fba_fee - (req.product_cost or 0.0), 2)
        gross_margin = round(gross_profit / price, 4) if price else 0.0
        roi = round(net_profit / total_cost, 4) if total_cost else 0.0

        # 保本售价：在费用率不变的前提下，令净利润为 0
        variable_rate = referral_rate + (req.advertising_rate or 0.0)
        fixed_cost = total_cost - referral_fee - ad_fee
        if variable_rate < 1:
            break_even = round(fixed_cost / (1 - variable_rate), 2)
        else:
            break_even = 0.0

        return ProfitCalculatorResponse(
            selling_price=price,
            referral_fee=referral_fee,
            fba_fulfillment_fee=fba_fee,
            first_leg_shipping=round(req.first_leg_shipping or 0.0, 2),
            monthly_storage_fee=round(req.monthly_storage_fee or 0.0, 2),
            advertising_fee=ad_fee,
            expected_return_loss=ret_loss,
            product_cost=round(req.product_cost or 0.0, 2),
            other_cost=round(req.other_cost or 0.0, 2),
            total_cost=total_cost,
            net_profit=net_profit,
            net_margin=net_margin,
            gross_profit=gross_profit,
            gross_margin=gross_margin,
            roi=roi,
            break_even_price=break_even,
        )

    # ==================== 5.1 BSR 销量预测 ====================

    def estimate_sales_by_bsr(
        self,
        bsr_rank: int,
        marketplace: str = "US",
        category: Optional[str] = None,
        price: Optional[float] = None,
        category_top_monthly_sales: int = 60000,
        elasticity: float = 0.72,
        asin: Optional[str] = None,
    ) -> SalesEstimatorResponse:
        """
        基于 BSR 的月销量估算。

        模型：月销量 = 类目基准销量 × (BSR) ^ (-弹性系数)
        - category_top_monthly_sales：该类目 BSR=1 时的月销量基准（美国站畅销类目约 5~8 万件）
        - elasticity：衰减弹性，默认 0.72（经验值，越大衰减越快）
        """
        bsr = max(int(bsr_rank or 1), 1)
        base = max(int(category_top_monthly_sales or 60000), 1)
        k = float(elasticity or 0.72)

        monthly = base * math.pow(bsr, -k)
        monthly_int = max(int(round(monthly)), 1)

        revenue = round(monthly_int * price, 2) if price else None

        if bsr <= 1000:
            conf = "medium"
        elif bsr <= 20000:
            conf = "medium"
        else:
            conf = "low"

        notice = (
            "本结果为基于 BSR 幂律模型的本地估算，不消耗卖家精灵额度，也未调用官网销量预测接口。"
            "绝对精度依赖类目基准值(category_top_monthly_sales)与弹性系数(elasticity)，"
            "建议先用少量已知 ASIN 校准这两个参数后再用于决策。"
            "若需官网口径的精确销量，请使用竞品监控接口的 est_monthly_sales 字段。"
        )

        return SalesEstimatorResponse(
            asin=asin,
            marketplace=marketplace.upper(),
            bsr_rank=bsr,
            category=category,
            est_monthly_sales=monthly_int,
            est_daily_sales=max(int(round(monthly_int / 30)), 1),
            est_monthly_revenue=revenue,
            confidence=conf,
            method=f"幂律模型: {base} × {bsr}^(-{k})",
            notice=notice,
        )
