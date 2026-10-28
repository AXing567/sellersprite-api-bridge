"""探针：找到能渲染出收录检测表单的入口 URL"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

URLS = [
    ("plain", "https://www.sellersprite.com/v2/keyword-checker", None),
    ("market", "https://www.sellersprite.com/v2/keyword-checker", {"market": "US"}),
    ("cn-prefix", "https://www.sellersprite.com/cn/v2/keyword-checker", None),
    ("reverse-compare", "https://www.sellersprite.com/v2/keyword-research", None),
]

for tag, url, params in URLS:
    try:
        r = mgr.request("GET", url, params=params, timeout=120,
                        headers={"Referer": "https://www.sellersprite.com/cn/"})
        h = r.text
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        nform = len(re.findall(r"<form\b", h, re.I))
        has_search = "search-click-btn" in h
        has_kwform = 'form-condition-keyword-earch' in h
        has_thead = h.count("<thead")
        print(f"[{tag:16}] {r.status_code} len={len(h):7} forms={nform} "
              f"searchBtn={has_search} kwForm={has_kwform} thead={has_thead} "
              f"title={(t.group(1).strip() if t else '')[:26]!r}")
        if tag in ("plain", "market"):
            open(os.path.join(dbg, f"chk_{tag}.html"), "w", encoding="utf-8").write(h)
    except Exception as e:
        print(f"[{tag:16}] ERROR {e}")
