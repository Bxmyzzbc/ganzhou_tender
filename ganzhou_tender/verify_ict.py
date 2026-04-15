from classifier_ict import classify, get_keywords

# 测试只用标题判断
title_tests = [
    '安远县第十二幼儿园办公和信息化设备项目电子化询价公告',
    '安远县殡葬服务中心丧葬用品采购竞争性磋商公告',
    '安远县第一中学标准化考场广播系统竞争性磋商公告',
]

print('只用标题判断:')
for t in title_tests:
    result = classify(t)
    print(f'  [{result}] {t}')

print()

# 加上正文后（正文含合同、补充等常见词）
content = ' 七、合同履行期限：一年 补充事宜：见附件'
tests_with_content = [
    '安远县第十二幼儿园办公和信息化设备项目电子化询价公告' + content,
    '安远县第一中学标准化考场广播系统竞争性磋商公告' + content,
]

print('标题+正文（含合同/补充）:')
for t in tests_with_content:
    kw = get_keywords(t)
    result = classify(t)
    print(f'  [{result}] {t[:40]}...')
    print(f'     排除词: {kw["invalid_keywords"]}')
