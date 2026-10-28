"""
抓取 keyword-research / product-research / aba-reverse 页面，提取真实 ajax 端点与参数
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

pages = {
    "keyword_research": "https://www.sellersprite.com/v2/keyword-research",
    "aba_reverse": "https://www.sellersprite.com/v2/aba/reverse/search",
    "product_research": "https://www.sellersprite.com/v2/product-research",
}

for name, url in pages.items():
    r = mgr.request("GET", url, timeout=60)
    path = os.path.join(dbg, f"{name}.html")
    open(path, "w", encoding="utf-8").write(r.text)
    print(f"\n########## {name} status={r.status_code} len={len(r.text)}")

    # 提取 ajax url
    ajax_urls = set(re.findall(r'url\s*:\s*["\']([^"\']+)["\']', r.text))
    relevant = [u for u in ajax_urls if u.startswith("/")]
    print("ajax url:")
    for u in sorted(relevant)[:25]:
        print("   ", u)

    # 提取 form input name
    names = sorted(set(re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', r.text)))
    print("form inputs:", names[:30])
