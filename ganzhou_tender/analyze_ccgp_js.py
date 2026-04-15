"""
分析ccgp网站的API接口
"""

import requests
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.ccgp.gov.cn/",
}

time.sleep(15)

# 获取data4.js完整内容
resp = requests.get("https://search.ccgp.gov.cn/static/js/data4.js", headers=headers, timeout=30)
content = resp.text

# 保存
with open("ccgp_data4.js", "w", encoding="utf-8") as f:
    f.write(content)

print(f"JS长度: {len(content)}")

# 查找AJAX请求
import re

# 查找所有可能的URL
patterns = [
    r'ajax\s*\([^)]*\)',
    r'\$\.post\s*\([^)]*\)',
    r'\$\.get\s*\([^)]*\)',
    r'fetch\s*\([^)]*\)',
    r'url\s*:\s*["\']([^"\']+)["\']',
    r'["\'](https?://[^"\']+ccgp[^"\']*)["\']',
    r'["\'](/[^"\']*search[^"\']*)["\']',
    r'["\'](/[^"\']*bulletin[^"\']*)["\']',
    r'["\'](/[^"\']*list[^"\']*)["\']',
]

print("\n=== 查找AJAX和URL模式 ===")
for pattern in patterns:
    matches = re.findall(pattern, content)
    if matches:
        print(f"\n[{pattern[:40]}...]")
        for m in set(matches[:5]):
            print(f"  {m}")

# 查找page.js中的API
print("\n\n=== 分析page.js ===")
resp2 = requests.get("https://search.ccgp.gov.cn/static/js/page.js", headers=headers, timeout=30)
page_content = resp2.text
print(f"page.js长度: {len(page_content)}")

# 查找URL
for pattern in patterns:
    matches = re.findall(pattern, page_content)
    if matches:
        print(f"\n[{pattern[:40]}...]")
        for m in set(matches[:5]):
            print(f"  {m}")
