"""
网站：江西省公共资源交易平台 (jxsggzy.cn)
API接口：POST http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew
"""

import requests
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_today(date_str: str) -> bool:
    """
    判断日期字符串是否是今天
    
    支持格式：2026-04-15, 2026-04-15 00:00:00, 2026/04/15 等
    """
    if not date_str:
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 取前10位（YYYY-MM-DD）
    date_part = date_str[:10]
    
    return date_part == today


def parse_date(date_str: str) -> str:
    """
    将日期字符串转换为 YYYY-MM-DD 格式
    """
    if not date_str:
        return ""
    return date_str[:10]


class JxsggzyCrawler:
    """江西省公共资源交易平台爬虫"""
    
    BASE_URL = "http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew"
    KEYWORD = "赣州 招标"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Referer": "http://www.jxsggzy.cn/jiangxisearch/fullsearch.html"
        })
        # 禁用代理
        self.session.trust_env = False
    
    def fetch_page(self, page_index: int = 1, page_size: int = 50) -> Optional[Dict]:
        """
        获取指定页数据（不带日期过滤）
        
        Args:
            page_index: 页码（从1开始）
            page_size: 每页条数
        """
        pn = (page_index - 1) * page_size
        
        payload = {
            "token": "",
            "pn": pn,
            "rn": page_size,
            "sdt": "",  # 不限制开始日期
            "edt": "",  # 不限制结束日期
            "wd": self.KEYWORD,
            "inc_wd": "",
            "exc_wd": "",
            "fields": "title;content",
            "cnum": "",
            "sort": "{\"webdate\":0}",
            "ssort": "title",
            "cl": 500,
            "terminal": "",
            "condition": None,
            "time": None,
            "highlights": "title;content",
            "statistics": None,
            "unionCondition": None,
            "accuracy": "",
            "noParticiple": "1",
            "searchRange": None
        }
        
        logger.info(f"请求第 {page_index} 页，每页 {page_size} 条（关键词：{self.KEYWORD}）")
        
        try:
            resp = self.session.post(
                self.BASE_URL,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "result" not in data:
                logger.error(f"API返回数据格式异常: {data}")
                return None
                
            return data["result"]
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def parse_records(self, result: Dict) -> List[Dict]:
        """解析API返回的记录"""
        if not result or "records" not in result:
            return []
        
        records = []
        for r in result["records"]:
            link = r.get("linkurl", "")
            if link and not link.startswith("http"):
                link = "http://www.jxsggzy.cn" + link
            
            records.append({
                "title": self._clean_html(r.get("title", "")),
                "webdate": r.get("webdate", ""),
                "linkurl": link,
                "content": self._clean_html(r.get("content", "")),
                "categoryname": r.get("categoryname", ""),
                "zhaobiaofangshi": r.get("zhaobiaofangshi", ""),
                "xiaquname": r.get("xiaquname", ""),
                "infoid": r.get("infoid", ""),
            })
        
        return records
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    
    def crawl_today(self, page_size: int = 50) -> List[Dict]:
        """
        抓取当天的所有公告
        
        先抓取所有历史记录，再用代码过滤出今天的
        （因为API的日期过滤有bug，只能这样处理）
        
        Args:
            page_size: 每页条数，默认50
        
        Returns:
            当天的所有公告列表
        """
        today = datetime.now().strftime("%Y-%m-%d")
        all_records = []
        page_index = 1
        
        logger.info(f"开始抓取当天({today})的公告...")
        
        while True:
            result = self.fetch_page(page_index, page_size)
            if not result:
                logger.warning(f"第 {page_index} 页请求失败，停止抓取")
                break
            
            total_count = result.get("totalcount", 0)
            if page_index == 1:
                logger.info(f"总共 {total_count} 条记录（不限时间），开始筛选今天的...")
            
            records = self.parse_records(result)
            if not records:
                logger.info(f"第 {page_index} 页无数据，停止抓取")
                break
            
            # 过滤出今天的记录
            today_records = [r for r in records if is_today(r.get("webdate", ""))]
            
            all_records.extend(today_records)
            logger.info(f"第 {page_index} 页获取 {len(records)} 条，其中今天 {len(today_records)} 条，累计今天 {len(all_records)} 条")
            
            # 判断是否还有下一页
            if len(records) < page_size:
                logger.info("数据已全部抓取")
                break
            
            # 优化：如果这一页没有任何今天的记录，说明今天的已经全部过去了，停止
            if not today_records and page_index > 1:
                logger.info("后续页面无今天数据，停止抓取")
                break
            
            page_index += 1
        
        logger.info(f"抓取完成，共获取 {len(all_records)} 条今天的记录")
        return all_records
    
    def crawl_all(self, max_pages: int = 1, page_size: int = 5) -> List[Dict]:
        """兼容旧接口，实际调用 crawl_today"""
        return self.crawl_today(page_size=page_size)


def test():
    """测试函数"""
    crawler = JxsggzyCrawler()
    records = crawler.crawl_today()
    
    print(f"\n获取到 {len(records)} 条今天的记录：")
    for i, r in enumerate(records[:10], 1):
        print(f"\n--- 记录 {i} ---")
        print(f"标题: {r['title']}")
        print(f"时间: {r['webdate']}")
        print(f"链接: {r['linkurl']}")
        print(f"分类: {r['categoryname']}")


if __name__ == "__main__":
    test()
