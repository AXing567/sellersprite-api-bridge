"""
探测追踪看板页面数据加载方式
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.core.session_manager import SellerSpriteSession
from src.core.parser import pick_table

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pages = {
    "product_tracking": "https://www.sellersprite.com/v2/product-tracking",
    "keyword_tracking": "https://www.sellersprite.com/v2/keyword-tracking",
    "store_tracking": "https://www.sellersprite.com/v2/store-tracking",
}

for name, url in pages.items():
    prep = mgr.session.prepare_request(requests.Request("GET", url, params={"station": "US", "marketId": "1"}))
    r = mgr.request("GET", prep.url, timeout=90, headers={"Referer": url})
    open(os.path.join(base, "data", "debug", f"{name}.html"), "w", encoding="utf-8").write(r.text)
    t = pick_table(r.text, prefer_class="js-freeze-header", min_rows=1)
    print(f"\n=== {name} status={r.status_code} len={len(r.text)} ===")
    if t:
        print(f"  headers={len(t['headers'])} rows={len(t['rows'])}")
        print("  表头:", [h[:18] for h in t['headers'][:12]])
        for row in t["rows"][:2]:
            print("  行:", [c[:20] for c in row[:8]])
    else:
        print("  无表格")
