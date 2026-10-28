import requests, hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://www.sellersprite.com',
    'Referer': 'https://www.sellersprite.com/cn/w/user/login'
})

r_init = session.get('https://www.sellersprite.com/cn/w/user/login')
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

r_sign = session.post('https://www.sellersprite.com/w/user/signin', data=data, allow_redirects=False)
print("Status code:", r_sign.status_code)
print("Headers:", dict(r_sign.headers))
print("Body:", r_sign.text[:500])

