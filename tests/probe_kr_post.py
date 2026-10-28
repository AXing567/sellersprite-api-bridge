"""
尝试 POST 方式给 more 接口传 station，并测试关键词挖掘接口
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"

# 1. POST 带 form 传 station
print("=== 1. POST /more 带 station ===")
r = mgr.request("POST", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?pageNum=1",
                data={"station": "US", "marketId": "1", "pageNum": "1", "asin": ASIN, "v": "false"},
                timeout=90,
                headers={"Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
                         "X-Requested-With": "XMLHttpRequest"})
print(f"status={r.status_code} ct={r.headers.get('Content-Type')}")
print("head:", r.text[:400])

# 2. 变体接口
print("\n=== 2. GET /v2/keyword-reverse/variation/US/{asin} ===")
r2 = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-reverse/variation/US/{ASIN}", timeout=60,
                 headers={"Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
                          "X-Requested-With": "XMLHttpRequest"})
print(f"status={r2.status_code} ct={r2.headers.get('Content-Type')} len={len(r2.text)}")
print("head:", r2.text[:300])
