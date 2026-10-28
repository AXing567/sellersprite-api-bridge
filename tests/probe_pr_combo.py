"""
定位选产品返回多商品所需的参数组合
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import extract_tables

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://www.sellersprite.com/v2/product-research/monthly"

BASE = {
    "marketId": "1",
    "order.field": "total_units",
    "order.desc": "true",
    "symbol": "",
    "type": "monthly",
    "presetMode": "",
    "station": "US",
    "remainExportNum": "NEBD",
    "months": "",
    "showMode": "",
    "smallAndLight": "",
    "selectType": "1",
    "allChecked": "false",
    "weightUnit": "g",
    "sellerNations": "",
    "dimensionTypes": "",
    "page": "1",
    "size": "20",
    "monthName": "bsr_sales_nearly",
}

cases = [
    ("A: bsrIds[32]=hi + nodeIdPath", {**BASE, "bsrIds[32]": "hi",
        "nodeIdPath": "1055398:284507:289754:760384:289735:678496011"}),
    ("B: 仅 bsrIds[32]=hi", {**BASE, "bsrIds[32]": "hi",
        "nodeIdPath": ""}),
]

for label, payload in cases:
    r = mgr.request("POST", URL, data=payload, timeout=180,
                    headers={"Referer": "https://www.sellersprite.com/v2/product-research",
                             "Origin": "https://www.sellersprite.com"})
    tables = extract_tables(r.text)
    main = max(tables, key=lambda t: len(t["rows"])) if tables else None
    rows = main["rows"] if main else []
    asin_rows = [row for row in rows if re.search(r"B0[A-Z0-9]{8}", " ".join(row))]
    print(f"\n=== {label} ===")
    print(f"  status={r.status_code} len={len(r.text)} 表行数={len(rows)} 含ASIN行={len(asin_rows)}")
    for row in asin_rows[:3]:
        print("   ", [c[:26] for c in row[:9]])
