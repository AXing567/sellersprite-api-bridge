"""
查询当前账号的会员套餐、额度与站点配置
"""
import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()

# 1. 会员中心页面
r = mgr.request("GET", "https://www.sellersprite.com/v2/me", timeout=30)
print(f"/v2/me 状态: {r.status_code}, 长度: {len(r.text)}")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)
open(os.path.join(dbg, "me.html"), "w", encoding="utf-8").write(r.text)

# 提取套餐关键词
for kw in ["会员", "套餐", "到期", "剩余", "额度", "次数", "标准版", "高级版", "专业版", "免费"]:
    cnt = r.text.count(kw)
    if cnt:
        print(f"  '{kw}' 出现 {cnt} 次")

# 提取页面中可能的会员信息 json
m = re.findall(r'(?:vip|member|plan|package|expire|remain)[A-Za-z]*\s*[:=]\s*["\']?[\w\-\+\s:/]{2,40}', r.text, re.I)
print("\n会员相关片段(去重前20):")
for x in list(dict.fromkeys(m))[:20]:
    print("  ", x)

# 2. 剩余导出额度接口
r2 = mgr.request("GET", "https://www.sellersprite.com/v2/common/remain-export-num/", timeout=30)
print(f"\n/v2/common/remain-export-num/ -> {r2.status_code}: {r2.text[:400]}")
