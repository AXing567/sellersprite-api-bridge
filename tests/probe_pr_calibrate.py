"""探针：抓取选产品真实表头 + 一行完整单元格，用于校准列映射"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import extract_rows_loose

URL = "https://www.sellersprite.com/v2/product-research/monthly"
PARAMS = {
    "marketId": "1",
    "nodeIdPath": "1055398:284507:289754:760384:289735:678496011",
    "monthName": "bsr_sales_nearly",
    "page": "1",
    "size": "20",
    "order.field": "units",
    "order.desc": "true",
}

mgr = SellerSpriteSession()
resp = mgr.request("GET", URL, params=PARAMS, timeout=150, headers={"Referer": URL})
html = resp.text
print("status:", resp.status_code, "len:", len(html))

headers, rows, nodes = extract_rows_loose(html, min_cells=8)
print("\n=== HEADERS (%d) ===" % len(headers))
for i, h in enumerate(headers):
    print(f"  [{i}] {h!r}")

print("\n=== ROWS: %d ===" % len(rows))
if rows:
    r = rows[0]
    print("col count:", len(r))
    for i, c in enumerate(r):
        print(f"  ({i}) {c!r}")

    # DOM 细节
    print("\n=== DOM of row 0 ===")
    for i, td in enumerate(nodes[0]):
        a_dp = td.find("a", href=lambda h: h and "/dp/" in h)
        div_h1 = td.find("div", class_="h-1")
        img = td.find("img")
        print(f"  td[{i}] classes={td.get('class')} "
              f"a_dp={a_dp.get('href') if a_dp else None} "
              f"h1_title={div_h1.get('title') if div_h1 else None} "
              f"img={'Y' if img else None}")

print("\n=== ROWS 1-4 first 4 cells ===")
for i, r in enumerate(rows[1:5], start=1):
    print(f"  row{i}: {r[:4]}")

# 保存 HTML 供离线调试
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pr_dump.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("\nsaved:", out)
