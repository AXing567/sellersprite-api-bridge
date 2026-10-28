"""
验证关键词挖掘（服务端渲染表单 GET）是否能出数据
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()

params = {
    "station": "US",
    "marketId": "1",
    "keyword": "phone case",
    "keywordMatchType": "1",
    "order.field": "searches",
    "order.desc": "true",
    "page": "1",
    "size": "20",
    "supplement": "N",
    "usestatic": "R",
}
req = __import__("requests").Request("GET", "https://www.sellersprite.com/v2/keyword-research", params=params)
prep = mgr.session.prepare_request(req)

r = mgr.request("GET", prep.url, timeout=120,
                headers={"Referer": "https://www.sellersprite.com/v2/keyword-research"})
print(f"status={r.status_code} len={len(r.text)}")
print(f"<tr> 数量: {len(re.findall(r'<tr', r.text))}")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(base, "data", "debug", "kw_research_result.html")
open(out, "w", encoding="utf-8").write(r.text)
print("已保存:", out)

# 检查是否有真实数据特征
for kw in ["phone case", "月搜索量", "搜索量", "购买率", "SPR", "暂无", "无数据", "升级"]:
    print(f"  '{kw}': {r.text.count(kw)}")

# 找表格里的关键词单元格
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', r.text, re.S)
print(f"\n共 {len(rows)} 行")
for row in rows[:3]:
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
    if cells:
        cleaned = [re.sub(r'<[^>]+>', '', c).strip()[:40] for c in cells]
        print("  ", cleaned[:8])
