"""探针：找出选产品 GET 参数组合，定位导致空结果的那个参数"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import extract_rows_loose

URL = "https://www.sellersprite.com/v2/product-research/monthly"
NODE = "1055398:284507:289754:760384:289735:678496011"

COMBOS = [
    ("minimal", {"marketId": "1", "nodeIdPath": NODE, "monthName": "bsr_sales_nearly"}),
    ("+page", {"marketId": "1", "nodeIdPath": NODE, "monthName": "bsr_sales_nearly", "page": "1"}),
    ("+size", {"marketId": "1", "nodeIdPath": NODE, "monthName": "bsr_sales_nearly", "size": "20"}),
    ("+order", {"marketId": "1", "nodeIdPath": NODE, "monthName": "bsr_sales_nearly",
                "order.field": "units", "order.desc": "true"}),
    ("full", {"marketId": "1", "nodeIdPath": NODE, "monthName": "bsr_sales_nearly",
              "page": "1", "size": "20", "order.field": "units", "order.desc": "true"}),
]

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name, params in COMBOS:
    try:
        r = mgr.request("GET", URL, params=params, timeout=180,
                        headers={"Referer": "https://www.sellersprite.com/v2/product-research"})
        headers, rows, nodes = extract_rows_loose(r.text, min_cells=8)
        empty = "暂无结果" in r.text
        print(f"[{name:8}] status={r.status_code} len={len(r.text):8} rows={len(rows):3} "
              f"hdr={len(headers):2} empty={empty}")
        if rows and name == "minimal":
            open(os.path.join(base, "data", "debug", "pr_ok.html"), "w", encoding="utf-8").write(r.text)
    except Exception as e:
        print(f"[{name:8}] ERROR {e}")
