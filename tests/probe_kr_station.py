"""
穷举 station 传递方式，定位 keyword-reverse/more 的站点识别机制
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

ASIN = "B08N5WRWNW"
BASE = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?pageNum=1&v=false"


def probe(label, url, headers, cookies=None):
    mgr = __import__("src.core.session_manager", fromlist=["SellerSpriteSession"]).SellerSpriteSession()
    if cookies:
        for name, val, path in cookies:
            mgr.session.cookies.set(name, val, domain="www.sellersprite.com", path=path)
    r = mgr.request("GET", url, timeout=120, headers=headers)
    try:
        d = r.json()
        dto = d.get("dto") or {}
        print(f"[{label}] station={dto.get('station')} total={dto.get('total')} items={len(dto.get('items') or [])}")
    except Exception:
        print(f"[{label}] 非JSON {r.text[:120]}")


# 1. Referer 带 station
probe("Referer?station=US", BASE, {
    "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}?station=US",
    "X-Requested-With": "XMLHttpRequest",
})

# 2. 自定义请求头
probe("header X-Station", BASE, {
    "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
    "X-Requested-With": "XMLHttpRequest",
    "X-Station": "US",
    "X-Marketplace": "US",
})

# 3. cookie station=US (path=/)
probe("cookie station=US /", BASE, {
    "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
    "X-Requested-With": "XMLHttpRequest",
}, cookies=[("station", "US", "/"), ("market", "US", "/")])

# 4. URL 上直接带 station
probe("URL &station=US", BASE + "&station=US&market=US&marketplace=US", {
    "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
    "X-Requested-With": "XMLHttpRequest",
})
