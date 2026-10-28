from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.schemas.competitor import (
    CompetitorCoreInfoSchema,
    CompetitorSalesRankSchema,
    CompetitorPromotionSchema,
    CompetitorReviewsSchema,
    CompetitorTrafficKeywordsSchema,
    CompetitorAggregatedMonitorSchema
)
from src.modules.competitor.service import CompetitorService

router = APIRouter(prefix="/api/v1/competitor", tags=["竞品监控"])
service = CompetitorService()

# ----------------- 原子接口 1: 核心画像 -----------------
@router.get("/core-info", response_model=CompetitorCoreInfoSchema, summary="1. 核心画像与基础状态 (标题/主图/品牌/价格)")
def get_core_info(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """用于高频抓取 Listing 基础信息、图片、标题、当前 BuyBox 标价。"""
    data = service.get_core_info(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的核心画像数据")
    return data

# ----------------- 原子接口 2: 销量与BSR -----------------
@router.get("/sales-rank", response_model=CompetitorSalesRankSchema, summary="2. 销量与排名动向 (BSR排名/预估月销与月销额)")
def get_sales_rank(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """用于监控竞品出单能力与大类排名波动。"""
    data = service.get_sales_rank(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的销售排名数据")
    return data

# ----------------- 原子接口 3: 促销活动 -----------------
@router.get("/promotions", response_model=CompetitorPromotionSchema, summary="3. 促销与优惠券动向 (Coupon/秒杀/到手价)")
def get_promotions(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """用于监控竞品优惠券面额、秒杀活动和实际买家到手价。"""
    data = service.get_promotions(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的促销数据")
    return data

# ----------------- 原子接口 4: 评分与评价 -----------------
@router.get("/reviews", response_model=CompetitorReviewsSchema, summary="4. 口碑与评价监控 (星级/评论数/月新增)")
def get_reviews(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """用于监控竞品差评冲击、增评速度及总评论量。"""
    data = service.get_reviews(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的评价数据")
    return data

# ----------------- 原子接口 5: 流量词 -----------------
@router.get("/traffic-keywords", response_model=CompetitorTrafficKeywordsSchema, summary="5. 流量结构与关键词 (流量词总数/自然与广告分布)")
def get_traffic_keywords(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """用于监控竞品核心流量词位和广告/自然流量结构。"""
    data = service.get_traffic_keywords(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的流量词数据")
    return data

# ----------------- 顶层聚合接口 -----------------
@router.get("/monitor-summary", response_model=CompetitorAggregatedMonitorSchema, summary="【顶层聚合】单 ASIN 全维度监控聚合总览")
def get_monitor_summary(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US")
):
    """聚合上述所有维度的完整监控数据报表。"""
    data = service.get_aggregated_monitor(asin=asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到 ASIN: {asin} 的监控聚合数据")
    return data
