"""
内容去重模块
基于项目名称相似度判断是否为同一公告，支持多数据源
"""

import re
from typing import List, Dict
from difflib import SequenceMatcher


def extract_project_name(text: str) -> str:
    """
    从文本中提取项目名称（核心标识）
    
    移除：
    - 日期（2026.04.11 / 2026-04-11）
    - 时间（18:25:03）
    - 金额（元、万元）
    - 项目编号（JXBY2026-AY-C006）
    - 采购人/代理机构前缀
    - 公告类型后缀
    
    Args:
        text: 标题+内容的组合文本
    
    Returns:
        清理后的项目名称
    """
    if not text:
        return ""
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除日期格式（多种格式）
    text = re.sub(r'\d{4}[年.]\d{2}[月.]\d{2}[日]?', '', text)
    text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)  # 时间
    
    # 移除金额
    text = re.sub(r'\d{1,6}(?:[万能]?元|[万千百])', '', text)
    text = re.sub(r'¥?\d+\.?\d*', '', text)
    
    # 移除项目编号（多种格式）
    text = re.sub(r'[A-Z]{2,}\d{4}-[A-Z]{2}-\d{3,}', '', text)  # JXBY2026-AY-C006
    text = re.sub(r'[A-Z]{2,}\d{4}-[A-Z]{2}-\d{2}', '', text)  # JXBY2026-AY
    text = re.sub(r'[A-Z0-9]{10,}', '', text)  # 长编号
    
    # 移除常见前缀词
    prefixes = [
        r'^\[安远县\]',
        r'^关于',
        r'^采购人[：:]\S*',
        r'^代理机构[：:]\S*',
    ]
    for prefix in prefixes:
        text = re.sub(prefix, '', text, flags=re.I)
    
    # 移除常见后缀词
    suffixes = [
        r'竞争性磋商公告$',
        r'竞争性谈判公告$',
        r'公开招标公告$',
        r'邀请招标公告$',
        r'询价公告$',
        r'更正公告$',
        r'变更公告$',
        r'结果公告$',
        r'中标公告$',
        r'成交公告$',
        r'流标公告$',
        r'废标公告$',
    ]
    for suffix in suffixes:
        text = re.sub(suffix, '', text, flags=re.I)
    
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    
    Returns:
        0.0 ~ 1.0 的相似度
    """
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def is_same_project(record1: Dict, record2: Dict, threshold: float = 0.70) -> bool:
    """
    判断两条记录是否为同一项目
    
    Args:
        record1: 记录1 {title, content, url, ...}
        record2: 记录2 {title, content, url, ...}
        threshold: 相似度阈值，默认70%
    
    Returns:
        True=同一项目, False=不同项目
    """
    # 优先比较URL（如果完全相同，一定是同一项目）
    url1 = record1.get("url", "")
    url2 = record2.get("url", "")
    if url1 and url2 and url1 == url2:
        return True
    
    # 提取项目名称
    text1 = record1.get("title", "") + " " + record1.get("content", "")
    text2 = record2.get("title", "") + " " + record2.get("content", "")
    
    name1 = extract_project_name(text1)
    name2 = extract_project_name(text2)
    
    if not name1 or not name2:
        return False
    
    # 计算相似度
    similarity = calculate_similarity(name1, name2)
    
    return similarity >= threshold


def deduplicate_by_content(records: List[Dict], threshold: float = 0.70) -> List[Dict]:
    """
    对多条记录进行内容去重
    
    Args:
        records: 所有数据源的记录列表
        threshold: 相似度阈值，默认70%
    
    Returns:
        去重后的记录列表（保留第一条）
    """
    if not records:
        return []
    
    result = []
    
    for new_record in records:
        is_duplicate = False
        
        for existing in result:
            if is_same_project(new_record, existing, threshold):
                is_duplicate = True
                break
        
        if not is_duplicate:
            result.append(new_record)
    
    return result


def test():
    """测试内容去重"""
    # 模拟两个数据源的同一条公告
    record1 = {
        "title": "[安远县]江西省博远工程管理有限公司关于安远县殡葬服务中心丧葬用品等物资配送服务（项目编号：JXBY2026-AY-C006）的竞争性磋商公告",
        "content": "项目概况安远县殡葬服务中心丧葬用品等物资配送服务招标项目的潜在投标人应在江西省公共资源交易平台获取招标文件",
        "url": "http://www.jxsggzy.cn/jyxx/002006/002006001/20260412/f5744f03.html",
        "source": "jxsggzy"
    }
    
    record2 = {
        "title": "江西省博远工程管理有限公司关于安远县殡葬服务中心丧葬用品等物资配送服务（项目编号：JXBY2026-AY-C006）的竞争性磋商公告项目概况安远县殡葬服务中心丧葬用品等物资配送服务招标项目的潜在投标人应在江西省公共资源交易平台获取招标文件",
        "content": "",
        "url": "http://www.ccgp.gov.cn/cggg/dfgg/jzxtpgg/202604/t20260411_26392616.htm",
        "source": "ccgp"
    }
    
    # 测试提取项目名称
    text1 = record1.get("title", "") + " " + record1.get("content", "")
    text2 = record2.get("title", "") + " " + record2.get("content", "")
    
    name1 = extract_project_name(text1)
    name2 = extract_project_name(text2)
    
    print("=== 项目名称提取测试 ===")
    print(f"来源1: {record1['source']}")
    print(f"名称1: {name1}")
    print()
    print(f"来源2: {record2['source']}")
    print(f"名称2: {name2}")
    print()
    
    # 计算相似度
    similarity = calculate_similarity(name1, name2)
    print(f"相似度: {similarity:.2%}")
    print()
    
    # 判断是否同一项目
    same = is_same_project(record1, record2)
    print(f"判定为同一项目: {same}")
    print()
    
    # 测试去重功能
    print("=== 去重测试 ===")
    test_records = [
        record1,
        record2,
        {
            "title": "[安远县]安远县第一中学服务器采购招标公告",
            "url": "http://example.com/1",
            "source": "jxsggzy"
        },
        {
            "title": "安远县第一中学服务器采购招标公告项目概况见附件",
            "url": "http://example.com/2",
            "source": "ccgp"
        },
    ]
    
    result = deduplicate_by_content(test_records)
    print(f"去重前: {len(test_records)} 条")
    print(f"去重后: {len(result)} 条")
    for r in result:
        print(f"  - {r['title'][:40]}... [{r['source']}]")


if __name__ == "__main__":
    test()
