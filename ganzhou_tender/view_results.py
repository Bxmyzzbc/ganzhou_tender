import csv

with open('C:/Users/陈亮/.openclaw/workspace/anyuan_tender/output/anyuan_ict_20260413.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f'ICT项目共 {len(rows)} 条:')
    for i, r in enumerate(rows, 1):
        print(f"{i}. [{r['webdate']}] {r['title'][:60]}")
        print(f"   关键词: {r['ict_keywords']}")
