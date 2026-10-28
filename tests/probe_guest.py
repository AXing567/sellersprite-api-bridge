"""探针：游客态（无 Cookie）访问关键词反查，判断是否为账号权限限制"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
ASIN = "B0CMJTSVRW"

s = requests.Session()
s.headers.update({
    "User-Agent": UA,
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

PAGE = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}"
r = s.get(PAGE, timeout=120, params={"market": "US", "q": "N", "v": "false", "asin": ASIN})
h = r.text
t = re.search(r"<title>(.*?)</title>", h, re.S)
print("guest status", r.status_code, "len", len(h), "title", (t.group(1).strip() if t else None))
print("  u-datatable:", h.count("u-datatable"), "| <tr>:", len(re.findall(r"<tr\b", h, re.I)),
      "| 暂无:", h.count("暂无"), "| guestVisited:", h.count("guestVisited"))

MORE = f"{PAGE}/more"
r2 = s.get(MORE, timeout=150, params={"pageNum": 2, "v": "false"},
           headers={"Referer": PAGE, "X-Requested-With": "XMLHttpRequest"})
print("\nguest /more status", r2.status_code, "len", len(r2.text))
try:
    j = r2.json()
    dto = j.get("dto") or {}
    print("  code", j.get("code"), "station", dto.get("station"),
          "total", dto.get("total"), "items", len(dto.get("items") or []))
except Exception:
    print("  ", r2.text[:200])

# 关键词挖掘（已知可用）游客态对照
r3 = s.get("https://www.sellersprite.com/v2/keyword-research", timeout=120,
           params={"station": "US", "includeKeywords": "yoga mat"})
print("\nguest keyword-research:", r3.status_code, "len", len(r3.text),
      "| <form:", len(re.findall(r"<form\b", r3.text, re.I)))
