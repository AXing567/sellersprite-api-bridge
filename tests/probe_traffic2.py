"""
探查竞品流量词 / 关键词反查的真实数据端点（复用缓存 Cookie，不登录）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

ASIN = "B0CMJTSVRW"
mgr = SellerSpriteSession()

candidates = [
    ("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?pageNum=1"),
    ("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?page=1&size=20"),
    ("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/export?pageNum=1"),
    ("POST", "https://www.sellersprite.com/v2/keyword-reverse/list"),
]

for method, url in candidates:
    try:
        if method == "GET":
            r = mgr.request("GET", url, timeout=30, headers={
                "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
                "X-Requested-With": "XMLHttpRequest",
            })
        else:
            r = mgr.request("POST", url, timeout=30, data={
                "marketId": "1", "asin": ASIN, "page": 1, "size": 20
            }, headers={
                "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
                "X-Requested-With": "XMLHttpRequest",
            })
        ct = r.headers.get("Content-Type", "")
        print(f"\n[{method}] {url}")
        print(f"  status={r.status_code} ct={ct} len={len(r.text)}")
        head = r.text[:400].replace("\n", " ")
        print(f"  head: {head}")
    except Exception as e:
        print(f"\n[{method}] {url} -> 异常: {e}")
