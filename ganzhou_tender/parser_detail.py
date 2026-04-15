"""
详情页解析器
从招标公告详情页提取采购品目等信息
"""

import requests
import time
import logging
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def retry_request(max_retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i < max_retries - 1:
                        logger.warning(f"请求失败，重试 {i+1}/{max_retries}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"请求最终失败: {e}")
                        raise
        return wrapper
    return decorator


class DetailParser:
    """详情页解析器基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        self.session.trust_env = False
    
    @retry_request(max_retries=2, delay=1)
    def fetch_detail(self, url: str) -> Optional[str]:
        """获取详情页HTML"""
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return resp.text
        except Exception as e:
            logger.warning(f"获取详情页失败 {url}: {e}")
            return None


class JxsggzyDetailParser(DetailParser):
    """江西省公共资源交易平台详情页解析器"""
    
    def parse(self, url: str) -> Optional[Dict]:
        """
        解析详情页，提取采购品目等信息
        
        采购品目通常在页面正文中，包含"采购条目名称"等字段
        """
        html = self.fetch_detail(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 获取页面全部文本
        full_text = soup.get_text(separator="\n", strip=True)
        
        result = {
            "url": url,
            "purchase_items": [],  # 采购品目列表
            "budget": "",           # 预算金额
            "content_text": full_text[:2000],  # 前2000字符
        }
        
        # 提取采购品目（常见模式）
        # 格式：采购条目名称 | 采购品目 | 数量 | 单位 | 采购预算(人民币)
        items = []
        
        # 方法1：查找表格中的采购品目
        tables = soup.select("table")
        for table in tables:
            table_text = table.get_text()
            if "采购条目名称" in table_text or "采购品目" in table_text:
                rows = table.select("tr")
                for row in rows:
                    cells = [cell.get_text(strip=True) for cell in row.select("td")]
                    if len(cells) >= 2:
                        # 检查是否包含品目关键词
                        for cell in cells:
                            if any(k in cell for k in ["品目", "设备", "软件", "系统", "服务"]):
                                if cell not in items:
                                    items.append(cell)
        
        # 方法2：从正文中提取
        if not items:
            patterns = [
                r'采购品目[：:]\s*([^\n\r]+)',
                r'采购条目名称[：:]\s*([^\n\r]+)',
                r'采购内容[：:]\s*([^\n\r]+)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, full_text)
                for m in matches:
                    m = m.strip()
                    if len(m) > 2 and len(m) < 100 and m not in items:
                        items.append(m)
        
        result["purchase_items"] = items[:10]  # 最多保留10个
        
        # 提取预算金额
        budget_patterns = [
            r'预算[金额]?[：:]\s*([0-9,，.]+\s*元)',
            r'最高限价[：:]\s*([0-9,，.]+\s*元)',
            r'采购预算[（(]人民币[）)][：:]\s*([0-9,，.]+\s*元)',
        ]
        for pattern in budget_patterns:
            match = re.search(pattern, full_text)
            if match:
                result["budget"] = match.group(1)
                break
        
        return result


def test():
    """测试详情页解析"""
    parser = JxsggzyDetailParser()
    
    # 用之前抓到的链接测试
    test_urls = [
        "http://www.jxsggzy.cn/jyxx/002006/002006001/20260412/f5744f03-2ba6-4993-b59c-3ff247fa969a.html",
    ]
    
    for url in test_urls:
        print(f"\n解析: {url}")
        result = parser.parse(url)
        if result:
            print(f"预算: {result['budget']}")
            print(f"采购品目: {result['purchase_items']}")
            print(f"内容预览: {result['content_text'][:200]}...")


if __name__ == "__main__":
    test()
