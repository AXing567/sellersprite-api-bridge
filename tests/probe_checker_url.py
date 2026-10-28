"""探针：找出关键词收录检测正确的 URL 形态"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B0CMJTSVRW"
KWS = "yoga mat\ntoilet paper\tscreen protector"

CANDIDATES = [
    f"/v2/keyword-checker/1/{ASIN}",
    f"/v2/keyword-checker/us/{ASIN}",
    f"/v2/keyword-checker/US/{ASIN}/",
    f"/v2/keyword-checker/{ASIN}",
    f"/v2/keyword-checker/result/1/{ASIN}",
]

for path in CANDIDATES:
    url = "https://www.sellersprite.com" + path
    try:
        r = mgr.request("GET", url,
                        params={"market": "US", "asin": ASIN, "keywords": KWS},
                        timeout=150,
                        headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker"})
        t = re.search(r"<title>(.*?)</title>", r.text, re.S)
        print(f"[{path}] status={r.status_code} len={len(r.text)} "
              f"title={(t.group(1).strip() if t else '')[:30]!r}")
        if r.status_code == 200:
            flags = re.findall(r'name="flag"[^>]*value="([^"]*)"', r.text)
            print("   flag:", flags)
            print("   含 data-table:", "data-table" in r.text, "| name=market 值:",
                  re.findall(r'name="market"[^>]*value="([^"]*)"', r.text)[:3])
    except Exception as e:
        print(f"[{path}] ERROR {e}")
