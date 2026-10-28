import requests, hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://www.sellersprite.com/v2/keyword-reverse?asin=B0CMJTSVRW&market=US'
})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 探测 Script 95 里的接口
# 可能是 /v2/keyword-reverse/US/{asin}/more 或 /v2/keyword-reverse/US/more?asin=...
for test_url in [
    'https://www.sellersprite.com/v2/keyword-reverse/US/B0CMJTSVRW/more?pageNum=1',
    'https://www.sellersprite.com/v2/keyword-reverse/US//more?pageNum=1&asin=B0CMJTSVRW',
    'https://www.sellersprite.com/v2/keyword-reverse/US/more?pageNum=1&asin=B0CMJTSVRW',
    'https://www.sellersprite.com/v2/keyword-reverse/more?pageNum=1&asin=B0CMJTSVRW&market=US'
]:
    r = session.get(test_url)
    print(test_url, '-> status:', r.status_code, 'Content-Type:', r.headers.get('Content-Type'))
    if r.status_code == 200:
        print('  Prefix:', r.text[:300])
