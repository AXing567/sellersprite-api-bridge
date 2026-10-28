"""
用已保存的关键词挖掘结果页验证表头驱动解析
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import extract_tables, build_header_index

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "debug", "kw_research_result.html")
html = open(path, encoding="utf-8").read()

tables = extract_tables(html)
print(f"表格数: {len(tables)}")
for i, t in enumerate(tables):
    print(f"\n[{i}] classes={t['classes']} headers={len(t['headers'])} rows={len(t['rows'])}")

main = max(tables, key=lambda t: len(t["rows"]))
print(f"\n=== 主表 headers ({len(main['headers'])}) ===")
for i, h in enumerate(main["headers"]):
    print(f"  [{i}] {h[:50]}")

print(f"\n=== 前 5 行完整数据 ===")
for r in main["rows"][:5]:
    print()
    for i, c in enumerate(r):
        print(f"  [{i}] {c[:60]}")
    print("  " + "-" * 40)
