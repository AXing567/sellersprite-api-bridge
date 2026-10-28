"""探针：带上 market/q/v 参数请求关键词反查 more 端点"""
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
URL = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more"

VARIANTS = [
    ("q=N",          {"pageNum": 1, "v": "false", "q": "N", "market": "US", "asin": ASIN}),
    ("q=N&page2",    {"pageNum": 2, "v": "false", "q": "N", "market": "US", "asin": ASIN}),
    ("no-q",         {"pageNum": 2, "v": "false", "market": "US", "asin": ASIN}),
    ("q=LQ1",        {"pageNum": 1, "v": "false", "q": "LQ1", "market": "US", "asin": ASIN}),
]

for name, params in VARIANTS:
    try:
        r = mgr.request("GET", URL, params=params, timeout=150,
                        headers={
                            "Referer": f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}",
                            "X-Requested-With": "XMLHttpRequest",
                            "Accept": "application/json, text/javascript, */*; q=0.01",
                        })
        j = r.json()
        dto = j.get("dto") or {}
        items = dto.get("items") or []
        print(f"[{name:12}] code={j.get('code')} station={dto.get('station')} total={dto.get('total')} items={len(items)}")
        if items:
            print("   keys:", list(items[0].keys()))
            print("   sample:", json.dumps(
                {k: items[0].get(k) for k in ("keywords", "keywordCn", "searches", "purchases",
                                              "purchaseRate", "trafficPercentage", "rank",
                                              "naturalRank", "adRank", "trends")},
                ensure_ascii=False)[:600])
            open(os.path.join(dbg, "kwrev_ok.json"), "w", encoding="utf-8").write(
                json.dumps(j, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[{name:12}] ERROR {e}")
