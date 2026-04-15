import re

with open('zfcg_test.html', 'rb') as f:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(f.read(), 'html.parser')

text = soup.get_text()

# 日期模式
date_pattern = r'(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'

# 提取所有日期的位置
dates = [(d.start(), d.group(1)) for d in re.finditer(date_pattern, text)]
print(f'找到 {len(dates)} 个日期')

# 标题模式 - 匹配完整的"XXX有限公司关于...公告"
title_pattern = r'([\u4e00-\u9fa5]*有限公司关于[^公告]+?公告)'

records = []
for title_match in re.finditer(title_pattern, text):
    title = title_match.group(1).strip()
    title = re.sub(r'\s+', ' ', title)
    
    # 找这个标题之后最近的日期
    title_end = title_match.end()
    next_date = None
    for pos, date_str in dates:
        if pos > title_end:
            next_date = date_str
            break
    
    if next_date:
        records.append({
            'title': title,
            'date': next_date
        })

print(f'\n提取到 {len(records)} 条记录：\n')
for i, r in enumerate(records):
    print(f'{i+1}. [{r["date"]}]')
    print(f'   {r["title"][:80]}...')
    print()
