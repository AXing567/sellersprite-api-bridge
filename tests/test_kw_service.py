"""
实测关键词挖掘服务（真实调用，验证参数与解析）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.keywords.service import KeywordService

svc = KeywordService()

print("=== 1. 关键词挖掘：包含词 phone case ===")
res = svc.research(keyword="phone case", page=1, size=10)
print(f"返回 {res.returned} 条, has_more={res.has_more}, notice={res.notice}")
for it in res.items[:5]:
    print(f"  {it.rank}. {it.keyword} | 中文={it.keyword_cn} | 月搜={it.monthly_search_volume} "
          f"| 购买率={it.purchase_rate} | 集中度={it.click_concentration} | PPC={it.ppc_bid} "
          f"| 需供比={it.supply_demand_ratio} | 商品数={it.product_count} | 均价={it.market_avg_price}")
