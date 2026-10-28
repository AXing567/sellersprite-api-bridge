from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional

from src.schemas.tools import (
    ProfitCalculatorRequest, ProfitCalculatorResponse,
    SalesEstimatorResponse,
)
from src.modules.tools.service import ToolsService

router = APIRouter(prefix="/api/v1/tools", tags=["实用算法工具"])
service = ToolsService()


@router.post(
    "/profit-calculator",
    response_model=ProfitCalculatorResponse,
    summary="5.2 FBA 利润计算器（佣金/配送费/仓储/广告/退货全拆解）",
)
def profit_calculator(req: ProfitCalculatorRequest = Body(...)):
    """
    输入售价、采购成本与各项费用，输出完整的成本拆解、毛利/净利、毛利率/净利率、
    ROI 以及保本售价。纯本地计算，不消耗卖家精灵额度。
    """
    try:
        return service.calc_profit(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"利润计算失败: {e}")


@router.get(
    "/sales-estimator",
    response_model=SalesEstimatorResponse,
    summary="5.1 BSR 销量预测（本地幂律模型，零额度消耗）",
)
def sales_estimator(
    bsr_rank: int = Query(..., ge=1, description="商品大类 BSR 排名"),
    marketplace: str = Query("US", description="站点代码"),
    price: Optional[float] = Query(None, description="售价，提供后会额外算出预估月销售额"),
    category: Optional[str] = Query(None, description="类目名称（仅用于标注）"),
    asin: Optional[str] = Query(None, description="商品 ASIN（仅用于标注）"),
    category_top_monthly_sales: int = Query(60000, ge=1, description="该类目 BSR=1 时的月销量基准，用于校准"),
    elasticity: float = Query(0.72, gt=0, le=2, description="衰减弹性系数，默认 0.72"),
):
    """
    用 BSR 幂律模型估算月销量。此接口为本地算法，不调用卖家精灵网页端，
    因此不消耗会员额度、不受风控影响。精度取决于两个可调参数，
    建议先用已知 ASIN 校准后再用于决策。

    需要官网口径的精确销量请用 `/api/v1/competitor/sales-rank`。
    """
    try:
        return service.estimate_sales_by_bsr(
            bsr_rank=bsr_rank, marketplace=marketplace, price=price,
            category=category, asin=asin,
            category_top_monthly_sales=category_top_monthly_sales,
            elasticity=elasticity,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"销量预测失败: {e}")
