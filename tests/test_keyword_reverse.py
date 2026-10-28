import requests, hashlib, re, json
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.sellersprite.com/v2/keyword-reverse'
})

# 登录
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 请求 /v2/keyword-reverse/US/?asin=B0CMJTSVRW
url = 'https://www.sellersprite.com/v2/keyword-reverse/US/'
params = {
    'asin': 'B0CMJTSVRW',
    'parentAsin': '',
    'size': '20',
    'page': '1'
}
r = session.get(url, params=params)
print('GET /v2/keyword-reverse/US/ status:', r.status_code)
print('Response length:', len(r.text))

# 提取关键数据：总流量词数、词列表
soup = BeautifulSoup(r.text, 'html.parser')
# 查找是否有表格
table = soup.find('table', class_='js-freeze-header') or soup.find('table')
if table:
    print('Found table in keyword reverse page!')
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr', recursive=False)
        print(f'Found {len(rows)} keyword rows!')
        if rows:
            for i, row in enumerate(rows[:5]):
                tds = [t.get_text(strip=True) for t in row.find_all('td', recursive=False)]
                print(f'Row {i}:', tds[:6])
else:
    print('No table found, search for keywords in text...')
    kw_matches = re.findall(r'data-keyword="([^"]+)"', r.text)
    print('Keywords found in data-keyword:', kw_matches[:10])
