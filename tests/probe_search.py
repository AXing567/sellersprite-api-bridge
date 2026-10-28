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

# 搜索带 ASIN 参数的请求页面
r_search = session.get('https://www.sellersprite.com/v2/competitor-lookup?asin=B0CMJTSVRW&market=US')
print("Status:", r_search.status_code)
# 检查是否直接渲染了数据，或者有内联 JSON 数据
json_matches = re.findall(r'(var|let|const)\s+([a-zA-Z0-9_]+)\s*=\s*(\{.*?\}|\[.*?\]);', r_search.text)
print("Data variables in HTML:", len(json_matches))
for kw, varname, val in json_matches:
    if any(k in varname.lower() for k in ['data', 'asin', 'item', 'result', 'list', 'product']):
        print(f"  {kw} {varname} = {val[:100]}...")

# 检查页面里是否有表单提交或查询方法
print("\nLook for search function in HTML:")
for line in r_search.text.split('\n'):
    if any(k in line for k in ['lookup', 'search', 'query', 'asin']) and 'function' in line:
        print(" ", line.strip()[:120])
