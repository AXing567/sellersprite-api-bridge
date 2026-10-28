"""端到端：通过 HTTP 验证三个原「受限」接口"""
import json
import sys
import requests

BASE = "http://127.0.0.1:8000"
NODE = "1055398:284507:289754:760384:289735:678496011"
ASIN = "B0CMJTSVRW"

# 本机访问必须绕开环境里的沙箱代理，否则 127.0.0.1 会被当成外网
SESSION = requests.Session()
SESSION.trust_env = False
SESSION.proxies = {"http": None, "https": None}


def show(title, url, params, brief):
    print("=" * 78)
    print(title)
    try:
        r = SESSION.get(url, params=params, timeout=300)
    except Exception as e:
        print("  请求异常:", e)
        return None
    print(f"  HTTP {r.status_code}  {r.url[:120]}")
    try:
        d = r.json()
    except Exception:
        print("  非JSON:", r.text[:300])
        return None
    brief(d)
    return d


def b_product(d):
    print(f"  returned={d.get('returned')} has_more={d.get('has_more')} "
          f"order={d.get('order_field')} month={d.get('month_name')}")
    print(f"  notice={d.get('notice')}")
    for i in d.get("items", [])[:3]:
        print(f"   - {i['asin']} | {(i.get('title') or '')[:36]} | ${i.get('price')} "
              f"| 销量{i.get('monthly_sales')} | 毛利{i.get('gross_margin')} "
              f"| BSR{i.get('bsr_rank')} | 评分{i.get('rating')}")


def b_reverse(d):
    print(f"  source={d.get('source')} total={d.get('total')} returned={d.get('returned')}")
    print(f"  notice={(d.get('notice') or '')[:90]}")
    for i in d.get("items", [])[:3]:
        print(f"   - {i['keyword'][:50]!r} rank={i.get('search_rank')} "
              f"搜索={i.get('searches')} 点击份额={i.get('click_share')}")


def b_checker(d):
    print(f"  source={d.get('source')} checked={d.get('checked')} indexed={d.get('indexed_count')}")
    print(f"  notice={(d.get('notice') or '')[:90]}")
    for i in d.get("items", []):
        print(f"   - {i['keyword'][:42]!r} indexed={i.get('is_indexed')} "
              f"evidence={(i.get('evidence') or '')[:52]}")


show("1) 选产品 /api/v1/product/filter", f"{BASE}/api/v1/product/filter",
     {"node_id_path": NODE, "size": 5}, b_product)

show("2) 关键词反查 /api/v1/keywords/reverse", f"{BASE}/api/v1/keywords/reverse",
     {"asin": ASIN, "size": 8}, b_reverse)

show("3) 关键词收录检测 /api/v1/keywords/checker", f"{BASE}/api/v1/keywords/checker",
     {"asin": ASIN, "keywords": ["wireless mics for iphone", "fuzzy microphone", "yoga mat"]}, b_checker)
