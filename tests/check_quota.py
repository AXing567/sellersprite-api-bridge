"""
查询账号各项功能剩余额度
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()

for url in [
    "https://www.sellersprite.com/v2/common/remain",
    "https://www.sellersprite.com/v3/api/client/valid-pay-status",
]:
    try:
        r = mgr.request("GET", url, timeout=30, headers={"Referer": "https://www.sellersprite.com/v2/me"})
        print(f"\n=== {url} ===")
        print(f"status={r.status_code} ct={r.headers.get('Content-Type')}")
        print(r.text[:1500])
    except Exception as e:
        print(f"\n{url} 异常: {e}")
