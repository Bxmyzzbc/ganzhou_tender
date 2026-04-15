"""
网站：江西省政府采购网 (zfcg.jxf.gov.cn)
使用Scrapling绕过Vue动态渲染，获取JavaScript渲染内容
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

from scrapling.fetchers import StealthyFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_today(date_str: str) -> bool:
    """
    判断日期字符串是否是今天
    
    支持格式：2026-04-15, 2026.04.15, 2026/04/15, 2026-04-15 10:30:00 等
    """
    if not date_str:
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 标准化日期格式
    # 2026.04.15 -> 2026-04-15
    normalized = re.sub(r'(\d{4})[./](\d{2})[./](\d{2})', r'\1-\2-\3', date_str)
    # 取前10位（YYYY-MM-DD）
    date_part = normalized[:10]
    
    return date_part == today


def parse_date(date_str: str) -> str:
    """
    将日期字符串转换为 YYYY-MM-DD 格式
    """
    if not date_str:
        return ""
    
    # 2026.04.15 -> 2026-04-15
    normalized = re.sub(r'(\d{4})[./](\d{2})[./](\d{2})', r'\1-\2-\3', date_str)
    return normalized[:10]


class ZfcgCrawler:
    """江西省政府采购网爬虫 - 使用Scrapling"""
    
    BASE_URL = "https://zfcg.jxf.gov.cn/maincms-web/fullSearchingJx"
    KEYWORD = "赣州市"
    SOURCE = "zfcg"
    
    def __init__(self):
        self.fetcher = StealthyFetcher()
    
    def fetch_page(self, page_index: int = 1) -> bytes:
        """使用Scrapling获取页面HTML"""
        url = f"{self.BASE_URL}?searchKey={self.KEYWORD}&pageIndex={page_index}"
        
        logger.info(f"抓取第 {page_index} 页（等待15秒让Vue渲染）...")
        
        try:
            page = self.fetcher.fetch(
                url=url,
                headless=True,
                timeout=120000,
                wait=8000
            )
            
            logger.info(f"页面长度: {len(page.body)} 字节")
            return page.body
            
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            return b""
    
    def parse_html(self, html: bytes) -> List[Dict]:
        """
        解析HTML，提取招标公告列表
        
        Args:
            html: 页面HTML字节
        
        Returns:
            公告列表，每条包含 title, webdate, linkurl, content, source
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        if self.KEYWORD not in text:
            logger.warning(f"页面中未找到关键词'{self.KEYWORD}'")
            return []
        
        records = []
        
        # 日期模式：2026-04-15 10:30:00
        date_pattern = r'(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        dates = [(d.start(), d.group(1)) for d in re.finditer(date_pattern, text)]
        
        # 标题模式 - 匹配完整的"XXX有限公司关于...公告/通知/结果/公示/变更"
        # 也匹配"XXX局关于..."等模式
        title_patterns = [
            r'([\u4e00-\u9fa5]*(?:有限公司|局|院|馆|校|处|部|集团)关于[^\n]{5,150}?(?:公告|通知|结果|公示|变更|更正|废标|终止))',
        ]
        
        all_titles = []
        for pattern in title_patterns:
            for m in re.finditer(pattern, text):
                title = m.group(1).strip()
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 15 and self.KEYWORD in title:
                    all_titles.append((m.start(), m.end(), title))
        
        # 按位置排序
        all_titles.sort(key=lambda x: x[0])
        
        # 为每个标题匹配日期
        for idx, (start, end, title) in enumerate(all_titles):
            # 找这个标题之后最近的日期
            next_date = None
            for pos, date_str in dates:
                if pos > end:
                    next_date = date_str
                    break
            
            if next_date:
                # 标准化日期
                pub_date = parse_date(next_date)
                
                records.append({
                    "title": title,
                    "webdate": pub_date,  # 格式化为 YYYY-MM-DD
                    "linkurl": "",  # zfcg页面Vue动态生成链接，无法获取
                    "content": "",  # zfcg搜索页没有内容摘要
                    "source": self.SOURCE,
                    "_raw_date": next_date,  # 保留原始日期用于调试
                })
        
        logger.info(f"解析出 {len(records)} 条记录")
        return records
    
    def crawl_today(self) -> List[Dict]:
        """
        抓取当天的所有公告
        
        Returns:
            当天的所有公告列表
        """
        all_records = []
        page_index = 1
        
        logger.info("开始抓取当天(zfcg)的公告...")
        
        while True:
            html = self.fetch_page(page_index)
            
            if not html:
                logger.warning(f"第 {page_index} 页获取失败，停止抓取")
                break
            
            records = self.parse_html(html)
            
            if not records:
                logger.info(f"第 {page_index} 页无数据，停止抓取")
                break
            
            # 检查这页是否有今天的记录
            has_today = any(is_today(r.get("webdate", "")) for r in records)
            
            if not has_today:
                # 这页没有今天的记录了，停止
                logger.info(f"第 {page_index} 页没有今天的记录，停止抓取")
                break
            
            all_records.extend(records)
            logger.info(f"第 {page_index} 页获取 {len(records)} 条有今天的记录，累计 {len(all_records)} 条")
            
            page_index += 1
        
        logger.info(f"抓取完成，共获取 {len(all_records)} 条记录")
        return all_records
    
    def crawl_all(self, max_count: int = 5) -> List[Dict]:
        """兼容旧接口，实际调用 crawl_today"""
        return self.crawl_today()


def test():
    """测试函数"""
    print("=" * 60)
    print("测试zfcg爬虫（Scrapling版）")
    print("=" * 60)
    
    crawler = ZfcgCrawler()
    records = crawler.crawl_today()
    
    print(f"\n获取到 {len(records)} 条记录：\n")
    for i, r in enumerate(records[:10], 1):
        print(f"{i}. [{r.get('webdate', '')}]")
        print(f"   标题: {r.get('title', '')[:70]}...")
        print(f"   URL: {r.get('linkurl', '(无)')}")
        print()


if __name__ == "__main__":
    test()
