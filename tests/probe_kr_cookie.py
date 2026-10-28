"""
设置 module-station cookie 后重试关键词反查
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"

# 关键：模拟前端写入 module-station cookie
cookies_to_set = [
    ("module-station-keyword-reverse", "US", "/v2/keyword-reverse"),
    ("module-station-keyword-research", "US", "/v2/keyword-research"),
    ("module-station-aba-reverse", "US", "/v2/aba/reverse"),
]
for name, val, path in cookies_to_set:
    mgr.session.cookies.set(name, val, domain="www.sellersprite.com", path=path)
    print(f"已设置 cookie: {name}={val} (path={path})")

# 重新请求
url = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?pageNum=1&v=false"
r = mgr.request("GET", url, timeout=120, headers={
    "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
    "X-Requested-With": "XMLHttpRequest",
})
print(f"\nstatus={r.status_code} ct={r.headers.get('Content-Type')} len={len(r.text)}")
try:
    d = r.json()
    dto = d.get("dto") or {}
    items = dto.get("items") or []
    print(f"code={d.get('code')} station={dto.get('station')} total={dto.get('total')} items={len(items)}")
    if items:
        print(f"\n首条字段: {list(items[0].keys())}")
        print(f"首条: {json.dumps(items[0], ensure_ascii=False)[:900]}")
except Exception as e:
    print("非 JSON:", r.text[:400])
