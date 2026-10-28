"""
GET /v2/product-research/monthly + nodeIdPath 验证
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
NODE = "1055398:284507:289754:760384:289735:678496011"

params = {
    "marketId": "1",
    "nodeIdPath": NODE,
    "monthName": "bsr_sales_nearly",
}

r = mgr.request("GET", URL, params=params, timeout=180,
                headers={"Referer": "https://www.sellersprite.com/v2/product-research"})
print(f"status={r.status_code} len={len(r.text)}")
open(os.path.join(base, "data", "debug", "pr_get_nodepath.html"), "w", encoding="utf-8").write(r.text)

tables = extract_tables(r.text)
for i, t in enumerate(tables):
    print(f"  table[{i}] classes={t['classes']} headers={len(t['headers'])} rows={len(t['rows'])}")

main = max(tables, key=lambda t: len(t["rows"])) if tables else None
if main:
    print(f"\n主表 headers={len(main['headers'])} rows={len(main['rows'])}")
    print("表头:", [h[:16] for h in main["headers"]])
    asin_rows = [row for row in main["rows"] if re.search(r"B0[A-Z0-9]{8}", " ".join(row))]
    print(f"含 ASIN 行数: {asin_rows and len(asin_rows)}")
    for row in asin_rows[:4]:
        print()
        for i, c in enumerate(row):
            if c:
                print(f"  [{i}] {c[:65]}")
