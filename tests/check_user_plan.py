import requests, hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://www.sellersprite.com/v2/welcome'
})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 访问用户个人中心 / 账号信息
r = session.get('https://www.sellersprite.com/v2/me')
print('Me status:', r.status_code)
for l in r.text.split('\n'):
    if any(k in l for k in ['会员', '套餐', '有效', '到期', '权限', '等级', 'vip', '点数']):
        print(' ', l.strip()[:100])
