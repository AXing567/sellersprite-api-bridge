import requests, re

session = requests.Session()
r = session.get("https://www.sellersprite.com/v2/competitor-lookup")
# 打印页面中所有的 script 标签内的文本（内联 js）
inline_scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', r.text, re.DOTALL)
print("Inline script blocks:", len(inline_scripts))

for i, s in enumerate(inline_scripts):
    if "competitor" in s or "ajax" in s or "fetch" in s or "api" in s or "asin" in s.lower():
        lines = [line.strip() for line in s.split('\n') if any(k in line for k in ['url', 'post', 'get', 'api', 'competitor', 'asin'])]
        if lines:
            print(f"\n--- Script {i} ---")
            for l in lines[:15]:
                print(" ", l[:120])
