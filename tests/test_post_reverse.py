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

# 提取表单 POST 提交 /v2/keyword-reverse/US/
# 看看 form-condition-search
r = session.get('https://www.sellersprite.com/v2/keyword-reverse')
data = {
    'market': 'US',
    'searchAsin': 'B0CMJTSVRW',
    'asin': 'B0CMJTSVRW'
}
r_post = session.post('https://www.sellersprite.com/v2/keyword-reverse/US/', data=data)
print('POST /v2/keyword-reverse/US/ status:', r_post.status_code, 'length:', len(r_post.text))

# 检查返回的 HTML 里是否有关键词
matches = re.findall(r'data-clipboard-text="([^"]+)"', r_post.text)
print('Keywords found in clipboard text:', len(matches), matches[:10])
