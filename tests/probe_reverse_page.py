import requests, hashlib, re, json
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# 登录
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 访问流量词反查页面 /v3/keyword-reverse 或 /v2/keyword-reverse
for page_url in ['https://www.sellersprite.com/v3/keyword-reverse', 'https://www.sellersprite.com/v2/keyword-reverse']:
    r = session.get(page_url)
    print(f"Page {page_url} status: {r.status_code}")
    if r.status_code == 200:
        # 寻找提交的 ajax 接口
        soup = BeautifulSoup(r.text, 'html.parser')
        forms = soup.find_all('form')
        for f in forms:
            print("  Form action:", f.get('action'), "id:", f.get('id'), "method:", f.get('method'))
        # 寻找包含 api 的 js 片段
        api_matches = set(re.findall(r'["\'](/v[0-9]/api/[^"\'\s\?]+|/api/v[0-9]/[^"\'\s\?]+)["\']', r.text))
        print("  API matches:", list(api_matches)[:10])
