import requests, hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://www.sellersprite.com/v2/tools/sales-estimator'
})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 测试 POST 传参
r1 = session.post('https://www.sellersprite.com/v2/tools/sales-estimator/asin.json', data={'station': 'US', 'asin': 'B0CMJTSVRW'})
print('POST ASIN status:', r1.status_code, 'Content-Type:', r1.headers.get('Content-Type'))
print('Response text:', r1.text[:300])

r2 = session.post('https://www.sellersprite.com/v2/tools/sales-estimator/bsr.json', data={'station': 'US', 'cid': 'electronics', 'bsr': '100'})
print('\nPOST BSR status:', r2.status_code, 'Content-Type:', r2.headers.get('Content-Type'))
print('Response text:', r2.text[:300])
