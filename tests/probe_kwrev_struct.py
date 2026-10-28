"""探针：关键词反查页结构 / 正确端点与站点参数"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

ASIN = "B0CMJTSVRW"

TARGETS = [
    ("rev_root", "https://www.sellersprite.com/v2/keyword-reverse", {"station": "US"}),
    ("rev_root_asin", "https://www.sellersprite.com/v2/keyword-reverse", {"station": "US", "asin": ASIN}),
    ("rev_path", f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}", {}),
]

for name, url, params in TARGETS:
    try:
        r = mgr.request("GET", url, params=params, timeout=120,
                        headers={"Referer": "https://www.sellersprite.com/v2/keyword-reverse"})
        h = r.text
        fn = os.path.join(dbg, f"kwrev_{name}.html")
        open(fn, "w", encoding="utf-8").write(h)
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        # 表单 action
        forms = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>', h)
        stat_hidden = re.findall(r'<input[^>]*name="station"[^>]*>', h)[:3]
        print(f"[{name}] status={r.status_code} len={len(h)} title={(t.group(1).strip() if t else '')[:40]}")
        print(f"    forms={forms[:4]}")
        print(f"    station_inputs={stat_hidden}")
        print(f"    GLOBAL出现={h.count('GLOBAL')} US出现={h.count('US')} final_url={r.url[:120]}")
    except Exception as e:
        print(f"[{name}] ERROR {e}")
