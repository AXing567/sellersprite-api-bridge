"""验证：选市场深度指标（毛利率/中国卖家占比/搜索购买比）是否回填"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.product.service import ProductService

svc = ProductService()
res = svc.research_market(marketplace="US", size=5, order_field="units")

print(f"returned={res.returned} has_more={res.has_more} notice={res.notice}")
for it in res.items[:5]:
    d = it.model_dump(exclude_none=True)
    keep = {k: d.get(k) for k in (
        "rank", "market_name", "node_id", "monthly_sales_total", "avg_price",
        "avg_gross_margin", "china_seller_ratio", "aplus_ratio", "return_rate",
        "search_purchase_ratio", "market_path_cn", "node_id_path") if d.get(k) is not None}
    print(json.dumps(keep, ensure_ascii=False)[:320])
