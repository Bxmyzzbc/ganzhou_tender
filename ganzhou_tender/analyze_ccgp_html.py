"""
分析ccgp HTML中的form action
"""

import requests
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.ccgp.gov.cn/',
}

time.sleep(10)

resp = requests.get('https://search.ccgp.gov.cn/', headers=headers, timeout=30)
print(f"状态: {resp.status_code}, 长度: {len(resp.text)}")

# 查找form
match = re.search(r'<form[^>]*name=["\']searchForm["\'][^>]*>', resp.text)
if match:
    print('找到form:', match.group())

# 查找action
match2 = re.search(r'action=["\']([^"\']+)["\']', resp.text)
if match2:
    print('action:', match2.group(1))

# 查找kw input
match3 = re.search(r'<input[^>]*name=["\']kw["\'][^>]*>', resp.text)
if match3:
    print('kw input:', match3.group())

# 查找所有form相关
forms = re.findall(r'<form[^>]*>', resp.text)
print(f'\n找到 {len(forms)} 个form')
for f in forms:
    print(f)
