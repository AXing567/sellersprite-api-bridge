import requests, hashlib, re, json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.sellersprite.com/v2/competitor-lookup',
    'X-Requested-With': 'XMLHttpRequest'
})

session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 提取 /v2/competitor-lookup/monthly
params = {
    'marketId': 'US',
    'asins': 'B0CMJTSVRW',
    'page': 1,
    'size': 20
}
r = session.get('https://www.sellersprite.com/v2/competitor-lookup/monthly', params=params)
print("Monthly lookup status:", r.status_code)
print("Content-Type:", r.headers.get('Content-Type'))
print("Response text prefix:", r.text[:300])

if 'application/json' in r.headers.get('Content-Type', ''):
    try:
        data = r.json()
        print("JSON keys:", data.keys() if isinstance(data, dict) else len(data))
    except Exception as e:
        print("JSON parse error:", e)
