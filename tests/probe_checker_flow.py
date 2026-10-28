"""探针：关键词收录检测 两步流程（POST 建任务 -> 轮询 result/{flag}）"""
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

FORM_VARIANTS = [
    ("market/asin/keywords", {"market": "US", "asin": ASIN, "keywords": "\n".join(KWS)}),
    ("station/asin/keyword", {"station": "US", "asin": ASIN, "keyword": "\n".join(KWS)}),
    ("market/asin/keyword", {"market": "US", "asin": ASIN, "keyword": ",".join(KWS)}),
]

for tag, data in FORM_VARIANTS:
    try:
        r = mgr.request("POST", URL, data=data, timeout=150,
                        headers={"Referer": "https://www.sellersprite.com/v2/keyword-checker",
                                 "Content-Type": "application/x-www-form-urlencoded"})
        h = r.text
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        flags = re.findall(r'name="flag"[^>]*value="([^"]*)"', h) or \
                re.findall(r'value="([^"]*)"[^>]*name="flag"', h)
        kwc = re.findall(r'name="keyWordCount"[^>]*value="([^"]*)"', h)
        print(f"[{tag}] status={r.status_code} len={len(h)} "
              f"title={(t.group(1).strip() if t else '')[:36]!r} flag={flags} kwCount={kwc}")
        if flags:
            open(os.path.join(dbg, "checker_result.html"), "w", encoding="utf-8").write(h)
            flag = flags[0]
            # 轮询
            for i in range(6):
                rr = mgr.request("GET", f"https://www.sellersprite.com/v2/keyword-checker/result/{flag}",
                                 timeout=120,
                                 headers={"Referer": r.url, "X-Requested-With": "XMLHttpRequest"})
                try:
                    j = rr.json()
                except Exception:
                    print("   非JSON:", rr.text[:120])
                    break
                res = j.get("result") or []
                print(f"   poll{i} result={len(res)}")
                if res:
                    print("   sample:", json.dumps(res[0], ensure_ascii=False)[:400])
                    open(os.path.join(dbg, "checker_result.json"), "w", encoding="utf-8").write(
                        json.dumps(j, ensure_ascii=False, indent=2))
                    break
                time.sleep(3)
            break
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
