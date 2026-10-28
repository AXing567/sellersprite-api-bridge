"""探针：离线解析已保存的选产品页面，校准列映射与 DOM 取值"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import extract_rows_loose

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(base, "data", "debug", "pr_ok.html"), encoding="utf-8").read()

headers, rows, nodes = extract_rows_loose(html, min_cells=8)
print("HEADERS (%d):" % len(headers))
for i, h in enumerate(headers):
    print(f"  [{i:2}] {h!r}")

print("\nROWS: %d" % len(rows))
r = rows[0]
print("cells in row0:", len(r))
for i, c in enumerate(r):
    print(f"  ({i:2}) {c!r}")

print("\n=== DOM row0 ===")
for i, td in enumerate(nodes[0]):
    parts = []
    a_dp = td.find("a", href=re.compile(r"/dp/"))
    if a_dp:
        parts.append("dp=" + a_dp.get("href"))
    for div in td.find_all("div", class_="h-1"):
        parts.append("h1=" + repr(div.get("title") or div.get_text(" ", strip=True))[:60])
    img = td.find("img")
    if img:
        parts.append("img=" + str(img.get("data-src") or img.get("src"))[:50])
    ba = td.find("a", href=re.compile(r"/stores/|/seller/"))
    if ba:
        parts.append("brand=" + ba.get_text(strip=True))
    print(f"  td[{i:2}] cls={td.get('class')} | " + " | ".join(parts))

print("\n=== row1 cells ===")
for i, c in enumerate(rows[1]):
    print(f"  ({i:2}) {c!r}")

print("\n=== row2 cells ===")
for i, c in enumerate(rows[2]):
    print(f"  ({i:2}) {c!r}")
