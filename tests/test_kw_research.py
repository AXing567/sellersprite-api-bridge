import requests, hashlib
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 测试关键词挖掘：wireless microphone
r = session.get('https://www.sellersprite.com/v2/keyword-research?q=wireless+microphone&market=US')
soup = BeautifulSoup(r.text, 'html.parser')
table = soup.find('table', class_='js-freeze-header') or soup.find('table')
if table:
    tbody = table.find('tbody')
    rows = tbody.find_all('tr', recursive=False) if tbody else []
    print(f'Total rows in keyword research: {len(rows)}')
    if rows:
        tds = [t.get_text(strip=True) for t in rows[0].find_all('td', recursive=False)]
        print('Keyword item 0:', tds[:8])
