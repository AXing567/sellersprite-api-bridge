"""探针：用 Cookie / 路径变体强制 station 解析为 US"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"
BH = {"X-Requested-With": "XMLHttpRequest",
      "Accept": "application/json, text/javascript, */*; q=0.01"}


def hit(tag, path, cookie=None, params=None):
    url = f"https://www.sellersprite.com/v2/keyword-reverse/{path}/{ASIN}/more"
    hdrs = dict(BH)
    hdrs["Referer"] = f"https://www.sellersprite.com/v2/keyword-reverse/{path}/{ASIN}"
    if cookie:
        hdrs["Cookie"] = cookie
    try:
        r = mgr.request("GET", url, params=params or {"pageNum": 2, "v": "false"},
                        timeout=150, headers=hdrs)
        j = r.json()
        dto = j.get("dto") or {}
        print(f"[{tag:22}] code={j.get('code')} station={dto.get('station')} "
              f"total={dto.get('total')} items={len(dto.get('items') or [])}")
    except Exception as e:
        print(f"[{tag:22}] ERROR {type(e).__name__} {e}")


# 1) 不同站点路径，看 station 是否回显
hit("path=JP", "JP")
hit("path=DE", "DE")

# 2) Cookie 强制
hit("cookie market=US", "US", cookie="market=US")
hit("cookie station=US", "US", cookie="station=US")
hit("cookie market=US;station=US", "US", cookie="market=US; station=US")
hit("cookie rank-market=US", "US", cookie="rank-market=US")
