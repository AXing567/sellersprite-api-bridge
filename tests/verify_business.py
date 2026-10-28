"""
业务接口连通性验证（复用已缓存 Cookie，不再登录）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
print(f"缓存 Cookie 是否已载入: {bool(mgr.session.cookies.get('Sprite-X-Token'))}")

# 1. 竞品反查
print("\n--- 测试竞品反查 /v2/competitor-lookup/monthly ---")
payload = {
    "marketId": "1",
    "station": "US",
    "competing": "true",
    "type": "monthly",
    "textareaValue": "B0CMJTSVRW",
    "order.field": "total_units",
    "order.desc": "true",
}
r = mgr.request("POST", "https://www.sellersprite.com/v2/competitor-lookup/monthly", data=payload, timeout=30)
print(f"状态码: {r.status_code}, 内容类型: {r.headers.get('Content-Type')}, 长度: {len(r.text)}")
if "ERR_GLOBAL_SESSION_EXPIRED" in r.text:
    print("!!! 会话失效")
elif "<table" in r.text:
    print(">>> 返回 HTML 表格，可正常解析")
else:
    print(">>> 响应片段:", r.text[:300])
