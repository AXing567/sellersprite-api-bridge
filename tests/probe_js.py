import requests, re

js_url = "https://www.sellersprite.com/assets-v2/js/product-asin-comparison.js?v202610230937"
r = requests.get(js_url)
print("product-asin-comparison.js length:", len(r.text))

# 提取里面的 API 路径
apis = set(re.findall(r'["\'](/v[0-9]/[^"\'\s\?]+|/w/[^"\'\s\?]+|/api/[^"\'\s\?]+)["\']', r.text))
print("Found API endpoints in comparison JS:")
for a in sorted(list(apis)):
    print(" ", a)

# 搜索 ajax post/get
ajax_calls = re.findall(r'url\s*:\s*["\']([^"\']+)["\']', r.text)
print("\nAjax URLs found:")
for a in set(ajax_calls):
    print(" ", a)
