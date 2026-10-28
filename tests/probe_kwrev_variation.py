"""探针：用 /v2/keyword-reverse/variation/US/{asin} 判断该 ASIN 是否有反查数据"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

ASINS = ["B0CMJTSVRW", "B08SGPWY8Z", "B0B4F4NHYW"]

for asin in ASINS:
    url = f"https://www.sellersprite.com/v2/keyword-reverse/variation/US/{asin}"
    try:
        r = mgr.request("GET", url, timeout=150,
                        headers={"Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{asin}",
                                 "X-Requested-With": "XMLHttpRequest"})
        print(f"[{asin}] status={r.status_code} len={len(r.text)}")
        try:
            j = r.json()
            vs = j.get("variations") or []
            print(f"   variations={len(vs)}")
            for v in vs[:5]:
                print("   ", {k: v.get(k) for k in ("asin", "total", "sku")})
            if vs:
                open(os.path.join(dbg, "kwrev_variation.json"), "w", encoding="utf-8").write(
                    json.dumps(j, ensure_ascii=False, indent=2))
        except Exception:
            print("   body:", r.text[:200].replace("\n", " "))
    except Exception as e:
        print(f"[{asin}] ERROR {e}")
