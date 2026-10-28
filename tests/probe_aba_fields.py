"""探针：ABA 出单词反查 原始字段结构（用于实现 反查 / 收录检测）"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

ASIN = "B0CMJTSVRW"
PAGE = "https://www.sellersprite.com/v2/aba/reverse/search"
MORE = "https://www.sellersprite.com/v2/aba/reverse/search/more"

# 先读周表名
r0 = mgr.request("GET", PAGE, params={"station": "US"}, timeout=120,
                 headers={"Referer": PAGE})
import re
weekly = sorted(set(re.findall(r"ara_\d{8}", r0.text)))
print("weekly tables:", weekly[-3:])
table = weekly[-1] if weekly else "ara_20261017"
mtable = table[:7]

r = mgr.request("GET", MORE, params={
    "station": "US", "table": table, "monthlyTable": mtable,
    "asin": ASIN, "order.field": "searchRank", "order.desc": "false",
    "reverseType": "monthly", "conversionType": "", "loadVariations": "false",
}, timeout=150, headers={"Referer": f"{PAGE}?asin={ASIN}&station=US",
                          "X-Requested-With": "XMLHttpRequest"})

j = r.json()
open(os.path.join(dbg, "aba_raw.json"), "w", encoding="utf-8").write(
    json.dumps(j, ensure_ascii=False, indent=2))
dto = j.get("dto") or j.get("data") or {}
print("dto keys:", list(dto.keys())[:20])
items = dto.get("items") or []
print("total:", dto.get("total"), "items:", len(items))
if items:
    print("\nitem[0] full:")
    print(json.dumps(items[0], ensure_ascii=False, indent=2)[:2500])
