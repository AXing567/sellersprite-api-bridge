"""探针：定位 keyword-reverse station 解析失败的真正原因"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

ASIN = "B08N5WRWNW"
BH = {"X-Requested-With": "XMLHttpRequest",
      "Accept": "application/json, text/javascript, */*; q=0.01"}


def show(tag, r):
    try:
        j = r.json()
    except Exception:
        print(f"[{tag}] 非JSON status={r.status_code} len={len(r.text)} :: {r.text[:150]}")
        return None
    dto = j.get("dto") or {}
    print(f"[{tag}] code={j.get('code')} station={dto.get('station')} "
          f"total={dto.get('total')} items={len(dto.get('items') or [])}")
    return j


# 1) POST 形式
try:
    url = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more"
    r = mgr.request("POST", url, data={"pageNum": "2", "v": "false"},
                    timeout=150, headers={**BH, "Referer": url})
    show("POST /more", r)
except Exception as e:
    print("[POST /more] ERROR", e)

# 2) 加 station 查询参数
try:
    url = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more"
    r = mgr.request("GET", url, params={"pageNum": 2, "v": "false", "station": "US",
                                        "market": "US", "marketId": "1"},
                    timeout=150, headers={**BH, "Referer": url})
    show("GET +station", r)
except Exception as e:
    print("[GET +station] ERROR", e)

# 3) path 变体
for seg in ["com", "USA", "1", "us"]:
    try:
        url = f"https://www.sellersprite.com/v2/keyword-reverse/{seg}/{ASIN}/more"
        r = mgr.request("GET", url, params={"pageNum": 2, "v": "false"},
                        timeout=150, headers={**BH, "Referer": url})
        show(f"path={seg}", r)
    except Exception as e:
        print(f"[path={seg}] ERROR {e}")

# 4) multiple 批量端点
try:
    url = "https://www.sellersprite.com/v2/keyword-reverse/multiple"
    r = mgr.request("GET", url, params={"market": "US", "asins": ASIN, "q": "N"},
                    timeout=150, headers={**BH, "Referer": url})
    print(f"[multiple] status={r.status_code} len={len(r.text)} ct={r.headers.get('content-type')}")
    print("   head:", r.text[:300].replace("\n", " "))
except Exception as e:
    print("[multiple] ERROR", e)

# 5) download 端点（常能反推参数名）
try:
    url = "https://www.sellersprite.com/v2/keyword-reverse/download"
    r = mgr.request("GET", url, params={"market": "US", "asin": ASIN, "q": "N"},
                    timeout=150, headers={**BH, "Referer": url})
    print(f"[download] status={r.status_code} len={len(r.text)} ct={r.headers.get('content-type')}")
    print("   head:", r.text[:200].replace("\n", " "))
except Exception as e:
    print("[download] ERROR", e)
