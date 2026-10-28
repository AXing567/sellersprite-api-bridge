"""探针：枚举 order.field 合法值"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import extract_rows_loose

URL = "https://www.sellersprite.com/v2/product-research/monthly"
NODE = "1055398:284507:289754:760384:289735:678496011"

BASE = {
    "marketId": "1",
    "selectType": "1",
    "nodeIdPath": NODE,
    "monthName": "bsr_sales_nearly",
    "weightUnit": "g",
    "filterSub": "false",
    "presetMode": "",
    "page": "1",
    "size": "20",
}

CANDIDATES = [
    "total_units", "total_amount", "bsr_rank", "price", "rating",
    "ratings", "profit", "profit_rate", "units_growth", "amount_growth", "bsr_growth",
]

mgr = SellerSpriteSession()
ok, bad = [], []
for f in CANDIDATES:
    params = dict(BASE)
    params["order.field"] = f
    params["order.desc"] = "true"
    try:
        r = mgr.request("GET", URL, params=params, timeout=180,
                        headers={"Referer": "https://www.sellersprite.com/v2/product-research"})
        _, rows, _ = extract_rows_loose(r.text, min_cells=8)
        if rows:
            ok.append((f, len(rows)))
            print(f"  OK   {f:18} rows={len(rows)}")
        else:
            bad.append(f)
            print(f"  --   {f:18} rows=0")
    except Exception as e:
        print(f"  ERR  {f:18} {e}")

print("\n有效字段:", [x[0] for x in ok])
print("无效字段:", bad)
