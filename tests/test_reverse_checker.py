"""验证：关键词反查（双通道） + 收录检测"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.keywords.service import KeywordService

svc = KeywordService()
ASIN = "B0CMJTSVRW"

rev = svc.reverse(asin=ASIN, marketplace="US", size=30)
print("=" * 70)
print(f"反转: source={rev.source} total={rev.total} returned={rev.returned}")
print(f"notice={rev.notice}")
for it in rev.items[:5]:
    print(" ", json.dumps(it.model_dump(exclude_none=True), ensure_ascii=False)[:280])

kws = [it.keyword for it in rev.items[:3]]
if rev.items:
    kws = [rev.items[0].keyword[:40], "yoga mat", "totally not a real keyword xyz"]

chk = svc.checker(asin=ASIN, keywords=kws, marketplace="US")
print("=" * 70)
print(f"收录: source={chk.source} checked={chk.checked} indexed={chk.indexed_count}")
print(f"notice={chk.notice}")
for it in chk.items:
    print(" ", json.dumps(it.model_dump(exclude_none=True), ensure_ascii=False)[:300])
