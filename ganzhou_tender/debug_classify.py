import requests
from classifier_ict import classify, get_keywords
import re

url = 'http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew'
payload = {
    'token': '', 'pn': 0, 'rn': 30, 'wd': '安远', 
    'sort': '{"webdate":0}',
    'fields': 'title;content', 'highlights': 'title;content', 'noParticiple': '1'
}
headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}

resp = requests.post(url, json=payload, headers=headers, timeout=15)
data = resp.json()
records = data['result']['records']

print(f"共 {len(records)} 条记录\n")

ict_list = []
non_ict_list = []

for i, r in enumerate(records, 1):
    # 清理HTML标签
    content = r.get('content', '')
    content_clean = re.sub(r'<[^>]+>', '', content)
    
    text = r.get('title', '') + ' ' + content_clean
    
    category = classify(text)
    
    if category == 'ICT招标类公告':
        ict_list.append(r)
        mark = 'ICT'
    else:
        non_ict_list.append(r)
        mark = 'NON'
    
    kw = get_keywords(text)
    print(f"{i}. [{mark}] {r.get('title', '')[:40]}...")
    if kw['ict_keywords']:
        print(f"   ICT词: {kw['ict_keywords']}")
    if kw['invalid_keywords']:
        print(f"   排除词: {kw['invalid_keywords']}")

print(f"\n统计: ICT={len(ict_list)}, NON_ICT={len(non_ict_list)}")
