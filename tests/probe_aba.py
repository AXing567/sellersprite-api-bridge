"""
验证 ABA 出单词反查接口（带 station=US）
"""
import os
import sys
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"

# 1. 打开带 asin 的 ABA 反查页面，提取最新周表名
r = mgr.request("GET", f"https://www.sellersprite.com/v2/aba/reverse/search?asin={ASIN}&station=US",
                timeout=60)
print(f"页面 status={r.status_code} len={len(r.text)}")

# 提取 ara_YYYYMMDD 周表
weekly = re.findall(r'ara_\d{8}', r.text)
monthly = re.findall(r'ara_\d{6}', r.text)
print(f"周表候选: {sorted(set(weekly))[-3:] if weekly else '无'}")
print(f"月表候选: {sorted(set(monthly))[-3:] if monthly else '无'}")

table = sorted(set(weekly))[-1] if weekly else "ara_20261017"
mtable = sorted(set(monthly))[-1] if monthly else "ara_202609"
print(f"选用 table={table} monthlyTable={mtable}")

# 2. 调用 more 接口
url = (f"https://www.sellersprite.com/v2/aba/reverse/search/more"
       f"?station=US&table={table}&monthlyTable={mtable}&asin={ASIN}"
       f"&order.field=searchRank&reverseType=&order.desc=false&conversionType=&loadVariations=false")
r2 = mgr.request("GET", url, timeout=120,
                 headers={"Referer": f"https://www.sellersprite.com/v2/aba/reverse/search?asin={ASIN}&station=US",
                          "X-Requested-With": "XMLHttpRequest"})
print(f"\nmore status={r2.status_code} ct={r2.headers.get('Content-Type')} len={len(r2.text)}")

try:
    d = r2.json()
    print(f"code={d.get('code')} message={d.get('message')}")
    data = d.get("data") or {}
    items = data.get("items") or []
    print(f"total={data.get('total')} items={len(items)}")
    if items:
        print(f"\n首条字段: {list(items[0].keys())}")
        print(f"首条内容: {json.dumps(items[0], ensure_ascii=False)[:800]}")
except Exception as e:
    print("解析失败:", e)
    print(r2.text[:600])
