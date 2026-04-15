"""
网站：中国政府采购网搜索 (search.ccgp.gov.cn)
使用Scrapling绕过反爬，获取JavaScript动态渲染内容
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
    
    支持格式：2026-04-15, 2026.04.15, 2026/04/15, 2026.04.15 10:30:00 等
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


class CcgpCrawler:
    """中国政府采购网爬虫 - 使用Scrapling"""
    
    # searchtype=2 + bidType=1：只显示公开招标公告
    BASE_URL = "https://search.ccgp.gov.cn/bxsearch"
    KEYWORD = "赣州"
    SOURCE = "ccgp"
    
    def __init__(self):
        self.fetcher = StealthyFetcher()
    
    def fetch_page(self, page_index: int = 1, start_time: str = "", end_time: str = "") -> str:
        """
        使用Scrapling获取页面HTML
        
        Args:
            page_index: 页码
            start_time: 开始日期，格式 YYYY:MM:DD
            end_time: 结束日期，格式 YYYY:MM:DD
        """
        today = datetime.now().strftime("%Y-%m-%d").replace('-', ':', 1).replace('-', ':')  # YYYY:MM:DD
        
        url = (
            f"{self.BASE_URL}"
            f"?searchtype=2"
            f"&page_index={page_index}"
            f"&bidSort=0"
            f"&buyerName="
            f"&projectId="
            f"&pinMu=0"
            f"&bidType=1"
            f"&dbselect=bidx"
            f"&kw={self.KEYWORD}"
            f"&start_time={start_time}"
            f"&end_time={end_time}"
            f"&timeType=0"
            f"&displayZone="
            f"&zoneId="
            f"&pppStatus=0"
            f"&agentName="
        )
        
        logger.info(f"抓取第 {page_index} 页（公开招标公告）...")
        
        try:
            # 使用Scrapling抓取，等待JS渲染
            page = self.fetcher.fetch(
                url=url,
                headless=True,
                timeout=60000,
                wait=5000
            )
            
            logger.info(f"页面长度: {len(page.body)} 字节")
            return page.body
            
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            return ""
    
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
        
        # 解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        records = []
        
        # 查找所有招标记录li
        lis = soup.find_all('li')
        logger.info(f"找到 {len(lis)} 个li元素")
        
        for li in lis:
            try:
                # 查找链接
                a = li.find('a', href=True)
                if not a:
                    continue
                
                href = a.get('href', '')
                # 必须是ccgp.gov.cn的链接
                if 'ccgp.gov.cn' not in href:
                    continue
                
                # 获取文本内容
                text = li.get_text(strip=True)
                
                # 必须包含赣州
                if self.KEYWORD not in text:
                    continue
                
                # 提取时间（格式：2026.04.11 或 2026-04-11）
                time_match = re.search(r'(2026[.\-]\d{2}[.\-]\d{2})', text)
                pub_time = time_match.group(1) if time_match else ''
                pub_date = parse_date(pub_time)
                
                # 清理标题（移除日期）
                title = re.sub(r'2026[.\-]\d{2}[.\-]\d{2}', '', text).strip()
                title = re.sub(r'\s+', ' ', title)
                
                records.append({
                    "title": title,
                    "webdate": pub_date,  # 格式化为 YYYY-MM-DD
                    "linkurl": href,
                    "content": "",  # ccgp搜索页没有摘要
                    "source": self.SOURCE,
                    "_raw_date": pub_time,  # 保留原始日期用于调试
                })
                
            except Exception as e:
                logger.warning(f"解析li失败: {e}")
                continue
        
        logger.info(f"解析出 {len(records)} 条记录")
        return records
    
    def crawl_today(self) -> List[Dict]:
        """
        抓取当天的所有公告（公开招标类型）
        
        Returns:
            当天的所有公告列表
        """
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        # ccgp 的日期格式是 YYYY:MM:DD
        today_param = today.strftime("%Y:%m:%d")
        
        all_records = []
        seen_urls: set = set()  # 用于检测重复（ccgp pagination 有bug）
        page_index = 1
        
        logger.info(f"开始抓取当天({today_str})的公告（公开招标）...")
        
        while True:
            html = self.fetch_page(page_index, start_time=today_param, end_time=today_param)
            
            if not html:
                logger.warning(f"第 {page_index} 页获取失败，停止抓取")
                break
            
            records = self.parse_html(html)
            
            if not records:
                logger.info(f"第 {page_index} 页无数据，停止抓取")
                break
            
            # 检测是否是重复页面（ccgp pagination 有bug，重复返回相同内容）
            new_urls = [r['linkurl'] for r in records if r['linkurl'] not in seen_urls]
            if len(new_urls) == 0:
                logger.info(f"第 {page_index} 页为重复内容，停止翻页")
                break
            
            # 过滤出今天的记录
            today_records = [r for r in records if is_today(r.get("webdate", ""))]
            
            if not today_records:
                logger.info(f"第 {page_index} 页没有今天的记录，停止抓取")
                break
            
            for r in records:
                if r['linkurl'] not in seen_urls:
                    seen_urls.add(r['linkurl'])
                    all_records.append(r)
            
            logger.info(f"第 {page_index} 页获取 {len(today_records)} 条今天的记录（新增 {len(new_urls)} 条），累计 {len(all_records)} 条")
            
            page_index += 1
        
        logger.info(f"抓取完成，共获取 {len(all_records)} 条记录")
        return all_records
    
    def crawl_all(self, max_count: int = 5) -> List[Dict]:
        """兼容旧接口，实际调用 crawl_today"""
        return self.crawl_today()


def test():
    """测试函数"""
    print("=" * 60)
    print("测试ccgp爬虫（Scrapling版）")
    print("=" * 60)
    
    crawler = CcgpCrawler()
    records = crawler.crawl_today()
    
    print(f"\n获取到 {len(records)} 条记录：\n")
    for i, r in enumerate(records[:10], 1):
        print(f"{i}. [{r['webdate']}] {r['title'][:60]}...")
        print(f"   URL: {r['linkurl'][:70]}...")
        print()


if __name__ == "__main__":
    test()
