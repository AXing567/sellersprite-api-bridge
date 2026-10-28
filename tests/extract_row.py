import requests, hashlib
from bs4 import BeautifulSoup
import json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})
r = session.post('https://www.sellersprite.com/v2/competitor-lookup/monthly', data={
    'marketId': '1', 'station': 'US', 'competing': 'true', 'type': 'monthly',
    'textareaValue': 'B0CMJTSVRW', 'order.field': 'total_units', 'order.desc': 'true'
})

soup = BeautifulSoup(r.text, 'html.parser')
table = soup.find('table', class_='js-freeze-header')
if table:
    tbody = table.find('tbody')
    rows = tbody.find_all('tr', recursive=False)
    print(f"Total rows in table: {len(rows)}")
    if rows:
        first_row = rows[0]
        tds = first_row.find_all('td', recursive=False)
        print(f"Total tds in first row: {len(tds)}")
        
        extracted = {}
        for idx, td in enumerate(tds):
            text_cleaned = ' '.join(td.get_text().split())
            print(f"TD[{idx}]: {text_cleaned[:80]}")
            extracted[f"col_{idx}"] = text_cleaned
            
        with open('sellersprite-api-bridge/tests/sample_row_tds.json', 'w', encoding='utf-8') as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)
else:
    print("No table found")
