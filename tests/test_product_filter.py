"""验证：选产品 service 能返回完整商品明细"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.product.service import ProductService

NODE = "1055398:284507:289754:760384:289735:678496011"

svc = ProductService()
res = svc.filter_products(marketplace="US", size=20, node_id_path=NODE, order_field="units")

print(f"returned={res.returned} has_more={res.has_more} month={res.month_name} order={res.order_field}")
print(f"notice={res.notice}")
for it in res.items[:6]:
    d = it.model_dump(exclude_none=True)
    print(json.dumps(d, ensure_ascii=False, indent=2))
    print("-" * 60)
