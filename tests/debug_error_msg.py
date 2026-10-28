import requests, hashlib
from bs4 import BeautifulSoup

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

r_sign = session.post('https://www.sellersprite.com/w/user/signin', data=data, allow_redirects=True)
soup = BeautifulSoup(r_sign.text, 'html.parser')
# 查找 alert 或 error 提示
alerts = soup.find_all(class_=lambda c: c and any(k in c.lower() for k in ['alert', 'error', 'danger', 'tip', 'msg', 'notice']))
for a in alerts:
    txt = a.get_text(strip=True)
    if txt:
        print("Alert element:", a.get('class'), "->", txt)

# 打印所有 script 中包含 message 或 error 的内容
scripts = soup.find_all('script')
for s in scripts:
    if s.string and any(k in s.string for k in ['账号', '密码', '错误', 'error', 'msg', '验证码', 'captcha']):
        lines = [line.strip() for line in s.string.split('\n') if any(k in line for k in ['账号', '密码', '错误', 'error', 'msg', '验证码', 'captcha'])]
        print("Script line matches:", lines[:5])

