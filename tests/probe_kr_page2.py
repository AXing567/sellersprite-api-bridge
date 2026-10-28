"""
1) 检查 more 请求实际发出的 cookie；2) 带 station 参数打开反查页面看首屏是否有数据
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"

mgr.session.cookies.set("module-station-keyword-reverse", "US",
                        domain="www.sellersprite.com", path="/v2/keyword-reverse")
print("当前 cookie jar:")
for c in mgr.session.cookies:
    print(f"  {c.name}={c.value[:30]} path={c.path} domain={c.domain}")

# 用 requests 的 prepare 看实际发出的 header
req = mgr.session.prepare_request(
    __import__("requests").Request(
        "GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}/more?pageNum=1&v=false")
)
print("\n实际发出的 Cookie 头:")
print(" ", req.headers.get("Cookie", "(空)")[:600])

# 带 station 打开页面
print("\n=== 打开 /v2/keyword-reverse/US/{asin}?station=US ===")
r = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}?station=US", timeout=90)
print(f"status={r.status_code} len={len(r.text)}")
trs = len(re.findall(r'<tr', r.text))
print(f"<tr> 数量: {trs}")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
open(os.path.join(base, "data", "debug", "kr_with_station.html"), "w", encoding="utf-8").write(r.text)
print("已保存 kr_with_station.html")

# 检查是否有 ASIN 行 / 无数据提示
for kw in ["无数据", "没有找到", "暂未收录", "keyword-td"]:
    print(f"  '{kw}': {r.text.count(kw)}")
