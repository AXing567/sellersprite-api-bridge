import requests, hashlib, re

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 探查销量预测计算器 /v2/tools/sales-estimator
r = session.get('https://www.sellersprite.com/v2/tools/sales-estimator')
print('Sales estimator page status:', r.status_code)
# 查找里面的 ajax 请求计算端点
urls = set(re.findall(r'["\'](/v[0-9]/[^"\'\s\?]+|/api/[^"\'\s\?]+)["\']', r.text))
print('APIs in sales estimator:', urls)
