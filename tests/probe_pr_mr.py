"""
验证选产品 / 选市场模块是否可出数据
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.core.session_manager import SellerSpriteSession
from bs4 import BeautifulSoup

mgr = SellerSpriteSession()

cases = [
    ("product-research", "https://www.sellersprite.com/v2/product-research", {
        "station": "US", "marketId": "1", "page": "1", "size": "20",
        "order.field": "units", "order.desc": "true", "monthName": "", "asins": "",
    }),
    ("market-research", "https://www.sellersprite.com/v2/market-research", {
        "station": "US", "marketId": "1", "page": "1", "size": "20",
        "order.field": "units", "order.desc": "true",
    }),
]

for name, url, params in cases:
    prep = mgr.session.prepare_request(requests.Request("GET", url, params=params))
    r = mgr.request("GET", prep.url, timeout=120, headers={"Referer": url})
    soup = BeautifulSoup(r.text, "html.parser")
    print(f"\n=== {name} status={r.status_code} len={len(r.text)} ===")
    found = False
    for t_idx, table in enumerate(soup.find_all("table")):
        rows = table.find_all("tr")
        data_rows = []
        for row in rows:
            cells = row.find_all("td")
            vals = [c.get_text(strip=True)[:22] for c in cells]
            if any(vals):
                data_rows.append(vals)
        if data_rows:
            found = True
            print(f"  table[{t_idx}] class={table.get('class')} 数据行={len(data_rows)}")
            for v in data_rows[:3]:
                print("     ", v[:7])
    if not found:
        print("  未找到数据行，检查空/加载提示:", [k for k in ["加载中", "暂无", "无数据", "升级"] if k in r.text])
