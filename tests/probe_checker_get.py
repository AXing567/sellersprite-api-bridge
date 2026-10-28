"""探针：关键词收录检测 GET 方式（表单默认 method=get）"""
import os
import re
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SellerSpriteSession

mgr = SellerSpriteSession()
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbg = os.path.join(base, "data", "debug")
os.makedirs(dbg, exist_ok=True)

ASIN = "B0CMJTSVRW"
KWS = ["yoga mat", "toilet paper", "screen protector"]
URL = f"https://www.sellersprite.com/v2/keyword-checker/US/{ASIN}"

r = mgr.request("GET", URL, params={"market": "US", "asin": ASIN, "keywords": "\n".join(KWS)},
                timeout=150, headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker"})
h = r.text
t = re.search(r"<title>(.*?)</title>", h, re.S)
print("status", r.status_code, "len", len(h), "title", (t.group(1).strip() if t else None))
open(os.path.join(dbg, "checker_get.html"), "w", encoding="utf-8").write(h)

flags = re.findall(r'name="flag"[^>]*value="([^"]*)"', h) or \
        re.findall(r'value="([^"]*)"[^>]*name="flag"', h)
print("flag:", flags)
print("kwCount:", re.findall(r'name="keyWordCount"[^>]*value="([^"]*)"', h))
print("含 data-table:", 'data-table' in h, "| 暂无:", h.count("暂无"))

# 打印表单字段，确认真正的 name
i = h.find('form-condition-keyword-earch')
if i > 0:
    j = h.find('</form>', i)
    frag = h[i:j if j > 0 else i + 6000]
    for m in re.finditer(r'<(?:input|textarea|select)[^>]*>', frag):
        tt = re.sub(r"\s+", " ", m.group(0))
        if "name=" in tt or "data-item" in tt:
            print("  field:", tt[:170])

if flags:
    flag = flags[0]
    for k in range(8):
        rr = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-checker/result/{flag}",
                         timeout=120,
                         headers={"Referer": r.url, "X-Requested-With": "XMLHttpRequest"})
        try:
            jj = rr.json()
        except Exception:
            print("  非JSON:", rr.text[:150])
            break
        res = jj.get("result") or []
        print(f"  poll{k} result={len(res)}")
        if res:
            print("  sample:", json.dumps(res[0], ensure_ascii=False)[:500])
            open(os.path.join(dbg, "checker_result.json"), "w", encoding="utf-8").write(
                json.dumps(jj, ensure_ascii=False, indent=2))
            break
        time.sleep(4)
