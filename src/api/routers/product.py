from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.schemas.product import ProductFilterResponse, MarketResearchResponse
from src.modules.product.service import ProductService
from src.core.session_manager import SessionExpiredError

router = APIRouter(prefix="/api/v1", tags=["3. 选产品与选市场"])
service = ProductService()


@router.get(
    "/product/filter",
    response_model=ProductFilterResponse,
    summary="3.1 产品库多维度选品（类目/销量/价格/毛利率/评分筛选）",
)
def product_filter(
    marketplace: str = Query("US", description="站点代码，默认 US"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数（官网分页 20 / 50 / 100）"),
    node_id_path: Optional[str] = Query(
        None,
        description="类目完整节点路径，冒号分隔多级，如 "
                    "1055398:284507:289754:760384:289735:678496011。"
                    "留空表示不限类目（全站）。可由 /market/research 返回的 node_id_path 获取",
    ),
    month: Optional[str] = Query(
        None,
        description="统计月份：留空=最近30天；也可传 202609 或 bsr_sales_monthly_202609",
    ),
    order_field: str = Query(
        "units",
        description="排序字段：units(月销量) / revenue(月销售额) / bsr(排名) / price / rating / profit(毛利率)",
    ),
    order_desc: bool = Query(True, description="是否降序"),
    # ---- 商品属性筛选 ----
    min_sales: Optional[int] = Query(None, description="近30天销量下限"),
    max_sales: Optional[int] = Query(None, description="近30天销量上限"),
    min_revenue: Optional[float] = Query(None, description="近30天销售额下限（美元）"),
    max_revenue: Optional[float] = Query(None, description="近30天销售额上限（美元）"),
    min_price: Optional[float] = Query(None, description="价格下限（美元）"),
    max_price: Optional[float] = Query(None, description="价格上限（美元）"),
    min_rating: Optional[float] = Query(None, description="评分星级下限，如 4.3"),
    max_rating: Optional[float] = Query(None, description="评分星级上限，如 5"),
    min_ratings: Optional[int] = Query(None, description="累计评分数下限"),
    max_ratings: Optional[int] = Query(None, description="累计评分数上限"),
    min_profit: Optional[float] = Query(None, description="毛利率下限，整数百分比，如 30 表示 30%"),
    max_profit: Optional[float] = Query(None, description="毛利率上限"),
    min_bsr: Optional[int] = Query(None, description="大类 BSR 下限（数值越小排名越前）"),
    max_bsr: Optional[int] = Query(None, description="大类 BSR 上限"),
    min_qa: Optional[int] = Query(None, description="Q&A 数量下限"),
    max_qa: Optional[int] = Query(None, description="Q&A 数量上限"),
    min_variations: Optional[int] = Query(None, description="变体数下限"),
    max_variations: Optional[int] = Query(None, description="变体数上限"),
    min_fba_fee: Optional[float] = Query(None, description="FBA 运费下限（美元）"),
    max_fba_fee: Optional[float] = Query(None, description="FBA 运费上限（美元）"),
    seller_type: Optional[str] = Query(None, description="配送方式：AMZ / FBA / FBM"),
    seller_nation: Optional[str] = Query(None, description="卖家所属地，如 CN（中国）"),
    keyword: Optional[str] = Query(None, description="标题包含关键词"),
    exclude_keyword: Optional[str] = Query(None, description="标题排除关键词"),
    best_seller_only: bool = Query(False, description="仅看 Best Seller 标"),
    new_release_only: bool = Query(False, description="仅看 New Release 标"),
):
    """
    对应网页版「选产品」：按类目节点 + 销量/价格/毛利率/评分等条件筛选高潜商品。

    **使用顺序建议**：先调 `/api/v1/market/research` 找到目标细分市场，
    取其 `node_id_path` 传给本接口，再叠加销量/毛利率等条件做二次筛选。

    **返回字段**（每个商品）：
    排名、ASIN、父 ASIN、标题、品牌、徽章(A+/视频/BS/AC)、价格、Q&A 数、
    BSR 排名与变化、近30天销量与增长率、近30天销售额与增长率、
    毛利率、FBA 运费、评分、月新增评分、累计评分数、留评率、
    上架日期、上架时长、发货方式、买家运费。
    """
    try:
        return service.filter_products(
            marketplace=marketplace, page=page, size=size,
            node_id_path=node_id_path, month=month,
            order_field=order_field, order_desc=order_desc,
            min_sales=min_sales, max_sales=max_sales,
            min_revenue=min_revenue, max_revenue=max_revenue,
            min_price=min_price, max_price=max_price,
            min_rating=min_rating, max_rating=max_rating,
            min_ratings=min_ratings, max_ratings=max_ratings,
            min_profit=min_profit, max_profit=max_profit,
            min_bsr=min_bsr, max_bsr=max_bsr,
            min_qa=min_qa, max_qa=max_qa,
            min_variations=min_variations, max_variations=max_variations,
            min_fba_fee=min_fba_fee, max_fba_fee=max_fba_fee,
            seller_type=seller_type, seller_nation=seller_nation,
            keyword=keyword, exclude_keyword=exclude_keyword,
            best_seller_only=best_seller_only,
            new_release_only=new_release_only,
        )
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"产品筛选失败: {e}")


@router.get(
    "/market/research",
    response_model=MarketResearchResponse,
    summary="3.2 细分市场分析（垄断度/新品占比/毛利率/价格带/退货率）",
)
def market_research(
    marketplace: str = Query("US", description="站点代码，默认 US"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    order_field: str = Query("units", description="排序字段: units(月销量) / revenue(月销售额) / bsr / price"),
    order_desc: bool = Query(True, description="是否降序"),
    node_id: Optional[str] = Query(None, description="上级类目节点 ID，用于查看该大类下的细分市场"),
):
    """
    对应网页版「选市场」：以细分市场为单位输出大盘数据。

    返回每个细分市场的：样本商品/品牌/卖家数、月总销量与月均销量、平均价格、
    平均评分与评分数、平均 BSR、FBA/AMZ/FBM 卖家结构、
    商品/品牌/卖家集中度（垄断程度）、新品数量与占比、商品总数、
    退货率与同类目均值，以及平均毛利率、A+ 页面占比、中国卖家占比、
    新品平均价格/销量/评分、平均重量体积、搜索购买比等深度指标。

    返回的 `node_id_path` 可直接作为 `/product/filter` 的入参。
    """
    try:
        return service.research_market(
            marketplace=marketplace, page=page, size=size,
            order_field=order_field, order_desc=order_desc, node_id=node_id,
        )
    except SessionExpiredError:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"市场分析失败: {e}")
