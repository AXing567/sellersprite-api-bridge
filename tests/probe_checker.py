"""探针：关键词收录检测页面结构（先看表单与是否有 SSR 结果表）"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

URL = "https://www.sellersprite.com/v2/keyword-checker"
r = mgr.request("GET", URL, timeout=120, headers={"Referer": "https://www.sellersprite.com/cn/"})
h = r.text
open(os.path.join(dbg, "kwchecker.html"), "w", encoding="utf-8").write(h)
t = re.search(r"<title>(.*?)</title>", h, re.S)
print("status", r.status_code, "len", len(h), "title", (t.group(1).strip() if t else None))

soup = BeautifulSoup(h, "html.parser")
for form in soup.find_all("form"):
    fid = form.get("id")
    action = form.get("action")
    names = []
    for el in form.find_all(["input", "select", "textarea"]):
        n = el.get("name")
        if n and n not in names:
            names.append(n)
    print(f"\nform id={fid} action={action} method={form.get('method')}")
    print("  fields:", names[:40])

print("\ntables:",
      [(tb.get("class"), len(tb.find_all("tr"))) for tb in soup.find_all("table")])
print("GLOBAL count:", h.count("GLOBAL"), "| 暂无:", h.count("暂无"), "| 很抱歉:", h.count("很抱歉"))
