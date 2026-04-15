"""
使用Scrapling提取ccgp招标数据
"""

from scrapling.fetchers import StealthyFetcher
from bs4 import BeautifulSoup
import re

# 抓取页面
fetcher = StealthyFetcher()
print("正在抓取页面...")
page = fetcher.fetch(
    url='https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&kw=%E5%AE%89%E8%BF%9C&timeType=2', 
    headless=True, 
    timeout=60000,
    wait=5000
)

print(f"页面长度: {len(page.body)} 字节")

# 用BeautifulSoup解析
soup = BeautifulSoup(page.body, 'html.parser')

# 查找所有招标记录
records = []
lis = soup.find_all('li')

print(f"共找到 {len(lis)} 个li元素")

for li in lis:
    a = li.find('a', href=True)
    if not a:
        continue
    
    href = a.get('href', '')
    if 'ccgp.gov.cn' not in href:
        continue
    
    text = li.get_text(strip=True)
    if '安远' not in text:
        continue
    
    # 提取时间
    time_match = re.search(r'(2026\.\d{2}\.\d{2})', text)
    pub_time = time_match.group(1).replace('.', '-') if time_match else ''
    
    # 清理标题
    title = re.sub(r'2026\.\d{2}\.\d{2}', '', text).strip()
    title = re.sub(r'\s+', ' ', title)
    
    records.append({
        'title': title,
        'url': href,
        'date': pub_time
    })

print(f"\n提取到 {len(records)} 条记录:\n")

for i, r in enumerate(records[:10], 1):
    print(f"{i}. [{r['date']}] {r['title'][:50]}...")
    print(f"   {r['url']}")
