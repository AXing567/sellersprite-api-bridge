"""
突破性验证：
1. 选产品真实端点是 POST /v2/product-research/monthly（不是 GET /v2/product-research）
2. 关键词反查需按表单完整参数 GET 页面后再调 more
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession
from src.core.parser import pick_table

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

# ============ 1. 选产品：POST /v2/product-research/monthly ============
print("=" * 60)
print("1. 选产品 POST /v2/product-research/monthly")
print("=" * 60)

payload = {
    "marketId": "1",
    "nodeIdPath": "",
    "order.field": "total_units",
    "order.desc": "true",
    "symbol": "",
    "type": "monthly",
    "presetMode": "",
    "station": "US",
    "remainExportNum": "NEBD",
    "months": "",
    "showMode": "",
    "smallAndLight": "",
    "selectType": "1",
    "allChecked": "false",
    "weightUnit": "g",
    "sellerNations": "",
    "dimensionTypes": "",
    "page": "1",
    "size": "20",
}

r = mgr.request("POST", "https://www.sellersprite.com/v2/product-research/monthly",
                data=payload, timeout=180,
                headers={"Referer": "https://www.sellersprite.com/v2/product-research",
                         "Origin": "https://www.sellersprite.com"})
print(f"status={r.status_code} ct={r.headers.get('Content-Type')} len={len(r.text)}")
open(os.path.join(dbg, "pr_monthly.html"), "w", encoding="utf-8").write(r.text)

if "ERR_GLOBAL_SESSION_EXPIRED" in r.text:
    print("!! 会话失效")
elif "<table" in r.text:
    t = pick_table(r.text, prefer_class="js-freeze-header", min_rows=1)
    if t:
        print(f">>> 找到表格 headers={len(t['headers'])} rows={len(t['rows'])}")
        print("表头:", [h[:16] for h in t["headers"][:16]])
        for row in t["rows"][:2]:
            print("行:", [c[:22] for c in row[:10]])
    else:
        print(">>> 有 table 标签但未提取到")
else:
    print(">>> 响应前 400:", r.text[:400])
