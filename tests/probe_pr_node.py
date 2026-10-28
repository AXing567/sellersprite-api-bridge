"""
用真实 nodeIdPath 验证选产品多商品返回
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import extract_tables

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NODE_PATH = "1055398:284507:289754:760384:289735:678496011"  # Tools > Hardware > Cabinet Hardware > Pulls

payload = {
    "marketId": "1",
    "nodeIdPath": NODE_PATH,
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
}

r = mgr.request("POST", "https://www.sellersprite.com/v2/product-research/monthly",
                data=payload, timeout=180,
                headers={"Referer": "https://www.sellersprite.com/v2/product-research",
                         "Origin": "https://www.sellersprite.com"})
print(f"status={r.status_code} len={len(r.text)}")
open(os.path.join(base, "data", "debug", "pr_nodepath.html"), "w", encoding="utf-8").write(r.text)

tables = extract_tables(r.text)
main = max(tables, key=lambda t: len(t["rows"]))
print(f"最大表格: headers={len(main['headers'])} rows={len(main['rows'])}")
print("表头:", [h[:14] for h in main["headers"]])

# 统计带 ASIN 的数据行
import re
asin_rows = 0
for row in main["rows"]:
    if re.search(r"B0[A-Z0-9]{8}", " ".join(row)):
        asin_rows += 1
print(f"含 ASIN 的行数: {asin_rows}")

for row in main["rows"][:6]:
    print()
    for i, c in enumerate(row):
        if c:
            print(f"  [{i}] {c[:70]}")
