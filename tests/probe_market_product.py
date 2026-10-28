"""
分析 market-research 表头与 product-research 正确参数
"""
import os
import sys
import re
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import pick_table

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 市场分析
url = "https://www.sellersprite.com/v2/market-research"
prep = mgr.session.prepare_request(requests.Request("GET", url, params={
    "station": "US", "marketId": "1", "page": "1", "size": "20",
    "order.field": "units", "order.desc": "true",
}))
r = mgr.request("GET", prep.url, timeout=120, headers={"Referer": url})
open(os.path.join(base, "data", "debug", "market_research.html"), "w", encoding="utf-8").write(r.text)

t = pick_table(r.text, prefer_class="js-freeze-header", min_rows=1)
print(f"=== market-research 表头 ({len(t['headers'])}) ===")
for i, h in enumerate(t["headers"]):
    print(f"  [{i}] {h[:60]}")

print(f"\n=== 前 3 行 ===")
for row in t["rows"][:3]:
    print()
    for i, c in enumerate(row):
        if c:
            print(f"  [{i}] {c[:70]}")

# 2. product-research 带 nodeId 试试
print("\n\n=== product-research 带 nodeId ===")
url2 = "https://www.sellersprite.com/v2/product-research"
prep2 = mgr.session.prepare_request(requests.Request("GET", url2, params={
    "station": "US", "marketId": "1", "page": "1", "size": "20",
    "order.field": "units", "order.desc": "true",
    "nodeId": "1055398", "nodeIdPath": "1055398",
    "monthName": "", "asins": "",
}))
r2 = mgr.request("GET", prep2.url, timeout=120, headers={"Referer": url2})
open(os.path.join(base, "data", "debug", "product_research2.html"), "w", encoding="utf-8").write(r2.text)
t2 = pick_table(r2.text, prefer_class="js-freeze-header", min_rows=1)
print(f"headers={len(t2['headers'])} rows={len(t2['rows'])}")
for i, h in enumerate(t2["headers"][:20]):
    print(f"  [{i}] {h[:50]}")
print("\n前 2 行:")
for row in t2["rows"][:2]:
    print("  ", [c[:25] for c in row[:10]])
