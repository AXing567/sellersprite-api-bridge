"""探针：枚举 /v2/keyword-checker 子路由，找非 404 的那条"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B0CMJTSVRW"

ROUTES = [
    f"/v2/keyword-checker/US/{ASIN}/result",
    f"/v2/keyword-checker/US/{ASIN}/download",
    f"/v2/keyword-checker/result/US/{ASIN}",
    f"/v2/keyword-checker/check/US/{ASIN}",
    f"/v2/keyword-checker/result",
    f"/v2/keyword-checker/download/US/{ASIN}",
]

for p in ROUTES:
    url = "https://www.sellersprite.com" + p
    try:
        r = mgr.request("GET", url, params={"market": "US", "asin": ASIN, "keywords": "yoga mat"},
                        timeout=120,
                        headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker",
                                 "X-Requested-With": "XMLHttpRequest"})
        body = r.text[:160].replace("\n", " ")
        print(f"[{p}] {r.status_code} len={len(r.text)} :: {body}")
    except Exception as e:
        print(f"[{p}] ERROR {e}")
