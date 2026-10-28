"""探针：收录检测最后两种可能路由（.html 后缀 / 基路由 POST）"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B0CMJTSVRW"

tests = [
    ("GET .html", "GET", f"https://www.sellersprite.com/v2/keyword-checker/US/{ASIN}.html", None),
    ("POST base", "POST", "https://www.sellersprite.com/v2/keyword-checker",
     {"market": "US", "asin": ASIN, "keywords": "yoga mat"}),
    ("POST base+flag", "POST", "https://www.sellersprite.com/v2/keyword-checker",
     {"station": "US", "asin": ASIN, "keyword": "yoga mat", "marketId": "1"}),
]

for tag, method, url, data in tests:
    try:
        if method == "GET":
            r = mgr.request("GET", url, params={"market": "US", "asin": ASIN, "keywords": "yoga mat"},
                            timeout=120,
                            headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker"})
        else:
            r = mgr.request("POST", url, data=data, timeout=120,
                            headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker"})
        t = re.search(r"<title>(.*?)</title>", r.text, re.S)
        flags = re.findall(r'name="flag"[^>]*value="([^"]*)"', r.text)
        print(f"[{tag}] {r.status_code} len={len(r.text)} "
              f"title={(t.group(1).strip() if t else '')[:28]!r} flag={flags} "
              f"form={'form-condition-keyword-earch' in r.text}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
