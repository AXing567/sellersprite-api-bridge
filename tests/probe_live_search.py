"""探针：/v2/live-search 实时搜索 —— 可用于实现收录检测与自然排名"""
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

URL = "https://www.sellersprite.com/v2/live-search"
r = mgr.request("GET", URL, params={"station": "US"}, timeout=120,
                headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker"})
h = r.text
t = re.search(r"<title>(.*?)</title>", h, re.S)
print("status", r.status_code, "len", len(h), "title", (t.group(1).strip() if t else None))
open(os.path.join(dbg, "live_search.html"), "w", encoding="utf-8").write(h)

print("forms:", len(re.findall(r"<form\b", h, re.I)))
for m in re.finditer(r"<form\b[^>]*>", h, re.I):
    print("  form:", re.sub(r"\s+", " ", m.group(0))[:180])

print("\najax urls:")
for m in sorted(set(re.findall(r"url\s*:\s*[\"']([^\"']+)[\"']", h))):
    if "live" in m or "search" in m:
        print("  ", m)

print("\n/v2/live-search refs:")
for m in sorted(set(re.findall(r"[\"'](/v2/live-search[^\"']*)", h))):
    print("  ", m)

for kw in ["data-item=keyword", "name=\"keyword\"", "name=\"station\"", "asins"]:
    print(kw, h.count(kw))
