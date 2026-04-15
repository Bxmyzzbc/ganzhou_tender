from scrapling.fetchers import StealthyFetcher
from bs4 import BeautifulSoup

fetcher = StealthyFetcher()
print('抓取页面（等待20秒）...')

page = fetcher.fetch(
    url='https://zfcg.jxf.gov.cn/maincms-web/fullSearchingJx?searchKey=%E5%AE%89%E8%BF%9C',
    headless=True,
    timeout=180000,
    wait=20000
)

print(f'页面长度: {len(page.body)} 字节')

# 检查是否包含安远
soup = BeautifulSoup(page.body, 'html.parser')
text = soup.get_text()
has_anyuan = '安远' in text
print(f'包含安远: {has_anyuan}')
print(f'文本长度: {len(text)}')

if has_anyuan:
    # 保存
    with open('zfcg_test2.html', 'wb') as f:
        f.write(page.body)
    print('已保存到 zfcg_test2.html')
