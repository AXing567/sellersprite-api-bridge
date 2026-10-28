"""探针：SSR 反查页是否已有数据行 + 尝试 header 鉴权"""
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
ASIN = "B08N5WRWNW"
PAGE = f"https://www.sellersprite.com/v2/keyword-reverse/US/{ASIN}"

r = mgr.request("GET", PAGE, params={"market": "US", "q": "N", "v": "false", "asin": ASIN},
                timeout=120, headers={"Referer": "https://www.sellersprite.com/v2/keyword-reverse"})
soup = BeautifulSoup(r.text, "html.parser")

tbl = soup.find("table", class_="u-datatable")
print("u-datatable found:", bool(tbl))
if tbl:
    ths = [th.get_text(" ", strip=True) for th in tbl.find_all("th")]
    tbody = tbl.find("tbody")
    trs = tbody.find_all("tr") if tbody else []
    print("ths:", ths)
    print("tbody tr count:", len(trs))
    if trs:
        print("first tr text:", re.sub(r"\s+", " ", trs[0].get_text(" ", strip=True))[:300])

for cls in ("lhy-num", "lhy-more", "lhy-no-more"):
    el = soup.find(class_=cls)
    print(f"{cls}:", (el.get_text(' ', strip=True)[:80] if el else None))

# 用 Sprite-X-Token 作为 header 再试 /more
tok = None
for c in mgr.session.cookies:
    if c.name == "Sprite-X-Token":
        tok = c.value
print("token present:", bool(tok))

for tag, extra in [
    ("hdr-token", {"Sprite-X-Token": tok or ""}),
    ("hdr-origin", {"Origin": "https://www.sellersprite.com"}),
]:
    url = f"{PAGE}/more"
    hdrs = {"X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": PAGE}
    hdrs.update(extra)
    try:
        rr = mgr.request("GET", url, params={"pageNum": 2, "v": "false"}, timeout=150, headers=hdrs)
        j = rr.json()
        dto = j.get("dto") or {}
        print(f"[{tag}] code={j.get('code')} msg={j.get('message')!r} station={dto.get('station')} "
              f"total={dto.get('total')} items={len(dto.get('items') or [])}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
