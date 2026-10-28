from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.schemas.tracking import (
    TrackedProductResponse, TrackedKeywordResponse, TrackedStoreResponse,
)
from src.modules.tracking.service import TrackingService
from src.core.session_manager import SessionExpiredError

router = APIRouter(prefix="/api/v1/tracking", tags=["常态化监控追踪"])
service = TrackingService()


@router.get("/products", response_model=TrackedProductResponse,
            summary="4.1 产品动态监控（读取网页端已建监控的商品）")
def tracking_products(
    marketplace: str = Query("US", description="站点代码"),
    tag: Optional[str] = Query(None, description="按标签/分组过滤"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """
    读取您在卖家精灵网页端「产品监控」中已添加的 ASIN 及其最新价格、BSR、销量、评分。

    注意：本接口只做读取。新建监控会消耗监控额度，需在网页端确认后操作。
    """
    try:
        return service.products(marketplace=marketplace, tag=tag, page=page, size=size)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"产品监控读取失败: {e}")


@router.get("/keywords", response_model=TrackedKeywordResponse,
            summary="4.2 关键词排名监控（自然位/广告位排名走势）")
def tracking_keywords(
    marketplace: str = Query("US", description="站点代码"),
    tag: Optional[str] = Query(None, description="按标签/分组过滤"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """读取网页端已建立的关键词排名监控，返回当前自然/广告排名与历史最佳排名。"""
    try:
        return service.keywords(marketplace=marketplace, tag=tag, page=page, size=size)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"关键词监控读取失败: {e}")


@router.get("/stores", response_model=TrackedStoreResponse,
            summary="4.3 店铺上新与竞店监控（在售商品数/近期上新）")
def tracking_stores(
    marketplace: str = Query("US", description="站点代码"),
    tag: Optional[str] = Query(None, description="按标签/分组过滤"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """读取网页端已建立的竞店监控，返回店铺在售商品数与近期上新数量。"""
    try:
        return service.stores(marketplace=marketplace, tag=tag, page=page, size=size)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"店铺监控读取失败: {e}")
