from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from src.schemas.keywords import (
    KeywordResearchResponse,
    AbaReverseResponse,
    KeywordReverseResponse,
    KeywordCheckerResponse,
)
from src.modules.keywords.service import KeywordService
from src.core.session_manager import SessionExpiredError

router = APIRouter(prefix="/api/v1/keywords", tags=["关键词挖掘与反查"])
service = KeywordService()


@router.get(
    "/research",
    response_model=KeywordResearchResponse,
    summary="2.1 关键词挖掘选词（月搜索量/购买率/PPC竞价/需供比）",
)
def keyword_research(
    keyword: Optional[str] = Query(None, description="包含的关键词，如 phone case；留空则返回该类目热词榜"),
    marketplace: str = Query("US", description="站点代码，默认 US"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    order_field: str = Query("searches", description="排序字段: searches(搜索量) / purchases(购买量) / growth(增长率) / cvsShareRate(转化份额)"),
    order_desc: bool = Query(True, description="是否降序"),
    min_search_volume: Optional[int] = Query(None, description="月搜索量下限"),
    max_search_volume: Optional[int] = Query(None, description="月搜索量上限"),
    min_purchase_rate: Optional[float] = Query(None, description="购买率下限，如 0.05 表示 5%"),
    exclude_keywords: Optional[str] = Query(None, description="排除的关键词，多个用空格或逗号分隔"),
):
    """
    对应网页版「关键词挖掘 / 关键词选品」。

    返回每个关键词的完整商业指标：月搜索量、日均搜索量、月购买量、购买率、
    展示/点击量、增长率、点击集中度、ABA 排名、货流值、PPC 建议竞价与竞价区间、
    需供比、在售商品数，以及搜索结果 Top 商品的价格/销量/评分概况。
    """
    try:
        return service.research(
            keyword=keyword,
            marketplace=marketplace,
            page=page,
            size=size,
            order_field=order_field,
            order_desc=order_desc,
            min_search_volume=min_search_volume,
            max_search_volume=max_search_volume,
            min_purchase_rate=min_purchase_rate,
            exclude_keywords=exclude_keywords,
        )
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"关键词挖掘失败: {e}")


@router.get(
    "/aba-reverse",
    response_model=AbaReverseResponse,
    summary="2.2 出单词反查（ABA 官方搜索词 / 点击份额 / 转化份额）",
)
def aba_reverse(
    asin: str = Query(..., description="目标 ASIN，例如 B08N5WRWNW"),
    marketplace: str = Query("US", description="站点代码，默认 US"),
    order_field: str = Query("searchRank", description="排序字段: searchRank(搜索排名) / clickShareRate / cvsShareRate"),
):
    """
    对应网页版「出单词反查」：查某个 ASIN 在亚马逊官方 ABA 榜单中的真实出单词，
    以及每个词对该 ASIN 的点击份额与转化份额。
    """
    try:
        return service.aba_reverse(asin=asin, marketplace=marketplace, order_field=order_field)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"出单词反查失败: {e}")


@router.get(
    "/reverse",
    response_model=KeywordReverseResponse,
    summary="2.2b 关键词反查（ASIN → 全量曝光关键词，双通道自动降级）",
)
def keyword_reverse(
    asin: str = Query(..., description="目标 ASIN，例如 B0CMJTSVRW"),
    marketplace: str = Query("US", description="站点代码，默认 US"),
    size: int = Query(50, ge=1, le=200, description="返回条数上限"),
    max_pages: int = Query(3, ge=1, le=10, description="主通道最多翻页数（每页约 100 条）"),
):
    """
    对应网页版「关键词反查」：输入 ASIN，拿到给它带来曝光/出单的全部关键词。

    **双通道设计**：
    - 主通道 `keyword-reverse`：网页版原接口，字段最全（含自然排名/广告排名）。
    - 备通道 `aba-reverse`：主通道为空时自动降级，返回官方 ABA 出单词口径数据。

    返回体的 `source` 字段会标明本次数据的实际来源，`notice` 会说明降级原因与字段差异。
    """
    try:
        return service.reverse(asin=asin, marketplace=marketplace,
                               size=size, max_pages=max_pages)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"关键词反查失败: {e}")


@router.get(
    "/checker",
    response_model=KeywordCheckerResponse,
    summary="2.3 关键词收录检测（自然位/广告位是否被收录）",
)
def keyword_checker(
    asin: str = Query(..., description="目标 ASIN，例如 B08N5WRWNW"),
    keywords: List[str] = Query(..., description="待检测关键词，可重复传参，如 ?keywords=phone case&keywords=case"),
    marketplace: str = Query("US", description="站点代码，默认 US"),
):
    """
    对应网页版「关键词收录检测」：检测某 ASIN 是否被亚马逊索引指定关键词。

    判定口径：调「关键词反查」拿到该 ASIN 的全部曝光关键词，再逐个比对传入词；
    命中即视为已收录，并回填该词的搜索排名/点击份额。
    每个词的判定依据写在 `evidence` 字段里。
    """
    try:
        return service.checker(asin=asin, keywords=keywords, marketplace=marketplace)
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"关键词收录检测失败: {e}")
