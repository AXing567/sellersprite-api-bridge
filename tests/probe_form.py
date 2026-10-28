import requests, hashlib

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})

# 查找页面中提交 form-condition-search 的地方
r = session.get('https://www.sellersprite.com/v2/competitor-lookup')
for line in r.text.split('\n'):
    if 'form-condition-search' in line and any(k in line for k in ['action', 'submit', 'post', 'ajax', 'attr']):
        print(" ", line.strip()[:140])

# 看看 form-condition-search 的 form 标签本身
import re
forms = re.findall(r'<form\b[^>]*id=["\']form-condition-search["\'][^>]*>', r.text)
print("\nForm tag:", forms)
