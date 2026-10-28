"""探针：确认产品监控页的真实表头（此前疑似与关键词监控页混淆）"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")

TARGETS = [
    ("product", "https://www.sellersprite.com/v2/product-tracking"),
    ("keyword", "https://www.sellersprite.com/v2/keyword-tracking"),
]

for tag, url in TARGETS:
    r = mgr.request("GET", url, params={"station": "US"}, timeout=120,
                    headers={"Referer": "https://www.sellersprite.com/v2/me"})
    h = r.text
    open(os.path.join(dbg, f"track_{tag}_fresh.html"), "w", encoding="utf-8").write(h)
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    print("=" * 20, tag, r.status_code, "len", len(h), "title", (t.group(1).strip() if t else None))
    for i, m in enumerate(re.finditer(r"<thead\b.*?</thead>", h, re.S)):
        if i > 1:
            break
        frag = m.group(0)
        cells = []
        for c in re.findall(r"<th\b[^>]*>(.*?)</th>", frag, re.S):
            txt = re.sub(r"<[^>]+>", "", c)
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                cells.append(txt.split(" ")[0] if len(txt) > 24 else txt)
        print(f"   thead[{i}]:", cells[:16])
