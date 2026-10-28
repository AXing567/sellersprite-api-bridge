"""
多参数组合 + 多 ASIN 定位 keyword-reverse/more 的正确调用方式
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
BASE = "https://www.sellersprite.com/v2/keyword-reverse"

tests = [
    ("B0CMJTSVRW", "?pageNum=1&v=false"),
    ("B0CMJTSVRW", "?pageNum=1&market=US"),
    ("B0CMJTSVRW", "?pageNum=1&station=US"),
    ("B0CMJTSVRW", "?pageNum=1&marketId=1"),
    ("B0113UZJE2", "?pageNum=1&v=false"),
]

for asin, qs in tests:
    url = f"{BASE}/US/{asin}/more{qs}"
    try:
        r = mgr.request("GET", url, timeout=60, headers={
            "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{asin}",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        })
        print(f"\n{asin} {qs} -> {r.status_code}")
        try:
            d = r.json()
            dto = d.get("dto") or {}
            items = dto.get("items") or []
            print(f"  code={d.get('code')} station={dto.get('station')} total={dto.get('total')} items={len(items)}")
            if items:
                print(f"  首条 keys: {list(items[0].keys())}")
                print(f"  首条内容: {json.dumps(items[0], ensure_ascii=False)[:500]}")
        except Exception:
            print("  非 JSON:", r.text[:200])
    except Exception as e:
        print(f"\n{asin} {qs} -> 异常: {e}")
