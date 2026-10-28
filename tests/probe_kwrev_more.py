"""探针：关键词反查 /more JSON 端点"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

ASIN = "B0CMJTSVRW"

for station in ["US", "GB", "DE"]:
    url = f"https://www.sellersprite.com/v2/keyword-reverse/{station}/{ASIN}/more"
    try:
        r = mgr.request("GET", url, params={"pageNum": 1, "v": "false"}, timeout=150,
                        headers={
                            "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/{station}/{ASIN}",
                            "X-Requested-With": "XMLHttpRequest",
                            "Accept": "application/json, text/javascript, */*; q=0.01",
                        })
        print(f"\n=== {station} status={r.status_code} len={len(r.text)} ct={r.headers.get('content-type')}")
        try:
            j = r.json()
        except Exception:
            open(os.path.join(dbg, f"kwrev_more_{station}.txt"), "w", encoding="utf-8").write(r.text)
            print("  非JSON:", r.text[:300].replace("\n", " "))
            continue
        open(os.path.join(dbg, f"kwrev_more_{station}.json"), "w", encoding="utf-8").write(
            json.dumps(j, ensure_ascii=False, indent=2))
        print("  code:", j.get("code"), "msg:", j.get("message") or j.get("msg"))
        dto = j.get("dto") or j.get("data") or {}
        if isinstance(dto, dict):
            print("  dto keys:", list(dto.keys())[:15])
            items = dto.get("items") or []
            print("  items:", len(items))
            if items:
                it = items[0]
                print("  item keys:", list(it.keys()))
                print("  sample:", json.dumps({k: it[k] for k in list(it.keys())[:14]},
                                             ensure_ascii=False)[:900])
    except Exception as e:
        print(f"=== {station} ERROR {e}")
