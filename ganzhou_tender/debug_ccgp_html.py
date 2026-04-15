"""
诊断ccgp页面HTML结构
"""

import requests
from bs4 import BeautifulSoup
import time

url = "https://search.ccgp.gov.cn/bxsearch"
params = {
    "searchtype": 1,
    "page_index": 1,
    "kw": "安远",
    "timeType": 2,
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://search.ccgp.gov.cn/",
}

print("请求ccgp页面...")

# 延迟10秒
time.sleep(10)

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

# 保存完整HTML到文件
with open("ccgp_debug.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

print("\n=== HTML内容前2000字符 ===")
print(resp.text[:2000])
