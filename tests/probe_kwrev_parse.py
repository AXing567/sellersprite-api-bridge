"""探针：离线解析关键词反查结果页"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import extract_rows_loose, extract_tables

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(base, "data", "debug", "kwrev_rev_path.html"), encoding="utf-8").read()

print("len", len(html), "tr", len(re.findall(r"<tr\b", html, re.I)),
      "thead", len(re.findall(r"<thead", html, re.I)))

for i, t in enumerate(extract_tables(html)):
    print(f"  table[{i}] cls={t['classes']} hdr={len(t['headers'])} rows={len(t['rows'])}")

headers, rows, nodes = extract_rows_loose(html, min_cells=6)
print("\nLOOSE headers(%d):" % len(headers))
for i, h in enumerate(headers):
    print(f"  [{i:2}] {h!r}")
print("\nrows:", len(rows))
for k in range(min(3, len(rows))):
    print(f"\n--- row{k} ({len(rows[k])} cells) ---")
    for i, c in enumerate(rows[k]):
        print(f"  ({i:2}) {c!r}")

# 找 form 的 action 与隐藏域
m = re.search(r'<form[^>]*action="(/v2/keyword-reverse[^"]*)"', html)
print("\nform action:", m.group(1) if m else None)

# 找更多参数线索：链接里带 station / asin 的
for mm in list(re.finditer(r'href="(/v2/keyword-reverse[^"]*)"', html))[:5]:
    print("  link:", mm.group(1)[:160])
