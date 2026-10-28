"""
抓取 keyword-reverse 页面并提取前端调用 more 接口的参数结构
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

ASIN = "B0CMJTSVRW"
mgr = SellerSpriteSession()

r = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}", timeout=30)
print(f"页面状态: {r.status_code}, 长度: {len(r.text)}")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(base, "data", "debug", "keyword_reverse_page.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"已保存: {out}")

# 提取更多端点引用
urls = sorted(set(re.findall(r'["\'](/v2/[a-zA-Z0-9\-_/]+)["\']', r.text)))
print("\n页面中出现的 /v2/ 端点:")
for u in urls:
    print("  ", u)

# 查找 more 调用上下文
idxs = [m.start() for m in re.finditer(r'/more', r.text)]
print(f"\n'/more' 出现 {len(idxs)} 次")
for i in idxs[:5]:
    print("  ...", r.text[max(0, i - 250):i + 120].replace("\n", " "))
    print("  ---")
