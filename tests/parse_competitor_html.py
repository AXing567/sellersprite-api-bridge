import requests, hashlib, re, json
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.sellersprite.com/v2/competitor-lookup'
})

# 1. 登录
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 2. 查询
data = {
    'marketId': '1',
    'station': 'US',
    'competing': 'true',
    'type': 'monthly',
    'textareaValue': 'B0CMJTSVRW',
    'order.field': 'total_units',
    'order.desc': 'true'
}
r = session.post('https://www.sellersprite.com/v2/competitor-lookup/monthly', data=data)

# 3. 检查 HTML 中是否有一个全局变量承载这一批竞品的完整 JSON 对象
scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', r.text, re.DOTALL)
found_items = False
for s in scripts:
    if 'data_arr' in s or 'itemArr' in s or 'items' in s:
        # 看看有没有 JSON 赋值
        matches = re.findall(r'(items|data_arr|list|products)\s*=\s*(\[\{.*?\}\]);', s, re.DOTALL)
        for name, val in matches:
            try:
                parsed = json.loads(val)
                print(f"Found JSON array '{name}' with {len(parsed)} items!")
                if len(parsed) > 0:
                    print("Sample keys of item 0:", list(parsed[0].keys())[:25])
                    found_items = True
                    with open('sellersprite-api-bridge/tests/sample_competitor_item.json', 'w', encoding='utf-8') as f:
                        json.dump(parsed[0], f, ensure_ascii=False, indent=2)
                    print("Saved sample to sellersprite-api-bridge/tests/sample_competitor_item.json")
            except Exception as e:
                pass

if not found_items:
    print("No direct JSON array found in scripts, checking tr/td attributes...")
    # 查找是否有带有 data-* 属性的 tr
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.find_all('tr', attrs={'data-asin': True})
    print(f"Found {len(rows)} table rows with data-asin!")
    if rows:
        print("Sample row data attrs:", list(rows[0].attrs.keys()))
