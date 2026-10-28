"""
检查 ABA 反查页面与关键词反查页面 SSR 是否含真实数据行
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from bs4 import BeautifulSoup

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"

# 1. ABA 反查页面（带 asin）
r = mgr.request("GET", f"https://www.sellersprite.com/v2/aba/reverse/search?asin={ASIN}&station=US&marketId=1",
                timeout=90)
print(f"=== ABA 页面 status={r.status_code} len={len(r.text)} tr={len(re.findall(r'<tr', r.text))}")
soup = BeautifulSoup(r.text, "html.parser")
for t_idx, table in enumerate(soup.find_all("table")):
    rows = table.find_all("tr")
    print(f"\n  table[{t_idx}] class={table.get('class')} rows={len(rows)}")
    for row in rows[:4]:
        cells = row.find_all(["td", "th"])
        vals = [c.get_text(strip=True)[:28] for c in cells][:7]
        if any(vals):
            print("    ", vals)

# 2. 关键词反查页面
r2 = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}?station=US&marketId=1",
                 timeout=90)
print(f"\n\n=== KR 页面 status={r2.status_code} len={len(r2.text)} tr={len(re.findall(r'<tr', r2.text))}")
soup2 = BeautifulSoup(r2.text, "html.parser")
for t_idx, table in enumerate(soup2.find_all("table")):
    rows = table.find_all("tr")
    print(f"\n  table[{t_idx}] class={table.get('class')} rows={len(rows)}")
    for row in rows[:4]:
        cells = row.find_all(["td", "th"])
        vals = [c.get_text(strip=True)[:28] for c in cells][:7]
        if any(vals):
            print("    ", vals)
