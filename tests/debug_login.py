import requests, hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://www.sellersprite.com',
    'Referer': 'https://www.sellersprite.com/cn/w/user/login'
})

r_init = session.get('https://www.sellersprite.com/cn/w/user/login')
print("Initial cookies:", session.cookies.get_dict())

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()

data = {
    'email': account,
    'password': pwd_md5,
    'autoLogin': 'Y',
    'callback': ''
}

r_sign = session.post('https://www.sellersprite.com/w/user/signin', data=data, allow_redirects=True)
print("After signin cookies:", session.cookies.get_dict())
print("After signin status:", r_sign.status_code, "URL:", r_sign.url)

# 用 session.get 请求 /v2/competitor-lookup/monthly 看看是否有效
r_lookup = session.get('https://www.sellersprite.com/v2/competitor-lookup/monthly?marketId=US&asins=B0CMJTSVRW')
print("Lookup status:", r_lookup.status_code)
if '登录' in r_lookup.text and '注册' in r_lookup.text and '退出' not in r_lookup.text:
    print("Lookup page indicates: NOT LOGGED IN")
else:
    print("Lookup page indicates: LOGGED IN OK")

# 测试请求 /v2/keyword-reverse/US/B0CMJTSVRW/more
token = session.cookies.get('Sprite-X-Token') or session.cookies.get('rank-login-user')
print("Token:", token)
headers = {
    'Referer': 'https://www.sellersprite.com/v2/keyword-reverse?asin=B0CMJTSVRW',
    'X-Requested-With': 'XMLHttpRequest'
}
if token:
    headers['Sprite-X-Token'] = token

r_more = session.get('https://www.sellersprite.com/v2/keyword-reverse/US/B0CMJTSVRW/more?pageNum=1', headers=headers)
print("More status:", r_more.status_code)
print("More content:", r_more.text[:400])

