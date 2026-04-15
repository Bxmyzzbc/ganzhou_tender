import requests
import json
from classifier_ict import is_ict, get_ict_keywords

url = 'http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew'
payload = {
    'token': '', 'pn': 0, 'rn': 10, 'wd': '安远', 
    'sort': '{"webdate":0}',
    'fields': 'title;content', 'highlights': 'title;content', 'noParticiple': '1'
}
headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}

resp = requests.post(url, json=payload, headers=headers, timeout=15)
data = resp.json()
records = data['result']['records']

print(f"测试 {len(records)} 条记录:\n")
ict_list = []
non_ict_list = []

for i, r in enumerate(records, 1):
    text = r.get('title', '') + ' ' + r.get('content', '')
    # 清理高亮标签
    text_clean = text.replace("<em style='color:red'>", "").replace("</em>", "")
    
    result = is_ict(text_clean)
    keywords = get_ict_keywords(text_clean)
    
    status = 'ICT' if result else 'NON'
    print(f"{i}. [{status}] {r.get('title', '')[:50]}...")
    if keywords:
        print(f"   关键词: {keywords}")
    
    if result:
        ict_list.append(r)
    else:
        non_ict_list.append(r)

print(f"\n统计: ICT={len(ict_list)}, NON_ICT={len(non_ict_list)}")
