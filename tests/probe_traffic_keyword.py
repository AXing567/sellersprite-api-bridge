import requests, hashlib, json, re

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

# 探查流量词页面
r = session.get('https://www.sellersprite.com/v2/competitor-lookup')
token = session.cookies.get('Sprite-X-Token')
print('Token:', token[:30] if token else None)

# 寻找流量词相关的 ajax 接口
apis = set(re.findall(r'["\'](/v[0-9]/[^"\'\s\?]+|/w/[^"\'\s\?]+|/api/[^"\'\s\?]+)["\']', r.text))
traffic_apis = [a for a in apis if any(k in a.lower() for k in ['traffic', 'keyword', 'flow', 'reverse'])]
print('Traffic related APIs in HTML:', traffic_apis)
