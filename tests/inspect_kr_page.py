import re

path = r"C:\Users\Administrator\Documents\AIProject\亚马逊卖家工具\sellersprite-api-bridge\data\debug\keyword_reverse_page.html"
html = open(path, encoding="utf-8").read()

tables = re.findall(r'<table[^>]*>', html)
print("table 标签:", len(tables))
for t in tables[:10]:
    print("  ", t[:200])

# 找 tbody tr 数量
print("\ntbody 数:", len(re.findall(r'<tbody', html)))
print("tr 数:", len(re.findall(r'<tr', html)))

# 找关键词字段名
for kw in ["keyword", "trafficPercentage", "searchVolume", "organic", "sponsored", "total"]:
    cnt = html.lower().count(kw.lower())
    print(f"'{kw}' 出现次数: {cnt}")

# 打印包含 reversingPageNum 的初始化配置 - 查找 reverse 相关的 js 变量
m = re.search(r'reversingPageNum\s*=\s*(\d+)', html)
print("\nreversingPageNum 初始值:", m.group(1) if m else "未找到")

# 找可能内嵌的 json 数据
for m in re.finditer(r'var\s+(\w+)\s*=\s*(\{.*?\});', html[:200000]):
    name = m.group(1)
    if any(k in name.lower() for k in ["reverse", "data", "item", "list"]):
        print(f"\n变量 {name} = {m.group(2)[:300]}")
