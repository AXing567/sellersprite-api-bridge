import requests, re

r = requests.get('https://www.sellersprite.com/assets-v2/js/keywords-miner.js?v202610261125')
print('Length:', len(r.text))
urls = set(re.findall(r'["\'](/v[0-9]/[^"\'\s\?]+|/api/[^"\'\s\?]+|/w/[^"\'\s\?]+)["\']', r.text))
for u in sorted(list(urls)):
    print(' ', u)
