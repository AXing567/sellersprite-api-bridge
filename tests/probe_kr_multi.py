"""
换热门 ASIN 与 ABA 接口对比，判断是权限问题还是数据问题
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()

# 1. 多个热门 ASIN 测 keyword-reverse
for asin in ["B08N5WRWNW", "B07FZ8S74R", "B0CMJTSVRW"]:
    url = f"https://www.sellersprite.com/v2/keyword-reverse/US/{asin}/more?pageNum=1&v=false"
    r = mgr.request("GET", url, timeout=90, headers={
        "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{asin}",
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        d = r.json()
        dto = d.get("dto") or {}
        print(f"[kr] {asin}: code={d.get('code')} station={dto.get('station')} total={dto.get('total')} items={len(dto.get('items') or [])} took={dto.get('took')}")
        items = dto.get("items") or []
        if items:
            print("   首条:", json.dumps(items[0], ensure_ascii=False)[:600])
    except Exception:
        print(f"[kr] {asin}: 非JSON {r.text[:200]}")

# 2. ABA 反查接口
print("\n--- ABA 反查 /v2/aba/reverse/search ---")
for asin in ["B08N5WRWNW"]:
    r = mgr.request("POST", "https://www.sellersprite.com/v2/aba/reverse/search", timeout=90,
                    data={"marketId": "1", "asin": asin, "page": 1, "size": 20},
                    headers={"Referer": "https://www.sellersprite.com/v2/keyword-reverse/US/" + asin,
                             "X-Requested-With": "XMLHttpRequest"})
    print(f"status={r.status_code} ct={r.headers.get('Content-Type')} len={len(r.text)}")
    print("  head:", r.text[:500])
