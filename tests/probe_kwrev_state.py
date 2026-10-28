"""探针：先按表单参数加载反查结果页建立会话状态，再取 /more"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

ASINS = ["B0CMJTSVRW", "B08N5WRWNW", "B09B8V1LZ3"]


def try_one(asin, page_num, with_q):
    page = f"https://www.sellersprite.com/v2/keyword-reverse/US/{asin}"
    pre = {"market": "US", "q": "N", "v": "false", "asin": asin} if with_q else {}
    r0 = mgr.request("GET", page, params=pre, timeout=120,
                     headers={"Referer": "https://www.sellersprite.com/v2/keyword-reverse"})
    more = f"{page}/more"
    r = mgr.request("GET", more,
                    params={"pageNum": page_num, "v": "false"},
                    timeout=150,
                    headers={
                        "Referer": r0.url,
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                    })
    try:
        j = r.json()
    except Exception:
        return f"非JSON len={len(r.text)} {r.text[:120]}"
    dto = j.get("dto") or {}
    return (f"code={j.get('code')} station={dto.get('station')} "
            f"total={dto.get('total')} items={len(dto.get('items') or [])}")


for asin in ASINS:
    for pn in (1, 2):
        for wq in (True, False):
            try:
                print(f"{asin} page={pn} with_q={wq} -> {try_one(asin, pn, wq)}")
            except Exception as e:
                print(f"{asin} page={pn} with_q={wq} -> ERROR {e}")
