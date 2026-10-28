import requests, hashlib, re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

session.get('https://www.sellersprite.com/cn/w/user/login')
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _creds import load_creds  # noqa: E402  凭证统一从 config.json / 环境变量读取
account, pwd_raw = load_creds()
pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
session.post('https://www.sellersprite.com/w/user/signin', data={'email': account, 'password': pwd_md5, 'autoLogin': 'Y'})
r_comp = session.get('https://www.sellersprite.com/v2/competitor-lookup')

api_urls = set(re.findall(r'["\'](/v[0-9]/api/[^"\'\s\?]+|/api/v[0-9]/[^"\'\s\?]+|/w/[^"\'\s\?]+)["\']', r_comp.text))
print("Found APIs in page HTML:", len(api_urls))
for u in sorted(list(api_urls))[:30]:
    print(" ", u)

# 打印页面里跟 competitor 有关的自定义 JS 文件
custom_js = [m for m in re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r_comp.text) if 'vendor' not in m and 'jquery' not in m]
print("\nCustom JS files:")
for js in custom_js:
    print(" ", js)
