"""
赣州市招标公告爬虫 - 主程序
多数据源：整合jxsggzy、ccgp两个数据源
抓取当天所有新发布的公告（公开招标类型），供AI分析筛选ICT项目
"""

import os
import json
import logging
from datetime import datetime

# 配置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入各模块
from crawler_jxsggzy import JxsggzyCrawler
from crawler_ccgp import CcgpCrawler
from content_dedup import deduplicate_by_content


class TenderCrawler:
    """招标公告爬虫主类"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化各数据源爬虫
        self.crawlers = {
            "jxsggzy": JxsggzyCrawler(),
            "ccgp": CcgpCrawler(),
        }
        
        # 统计
        self.stats = {
            "total_fetched": 0,
            "after_content_dedup": 0,
            "sources": {},
        }
    
    def _deduplicate_by_title(self, records: list) -> list:
        """标题去重：如果标题相同，只保留最新的一条"""
        seen_titles = {}
        result = []
        
        for r in records:
            title = r.get("title", "")
            date = r.get("publish_date", "")
            
            if title not in seen_titles:
                seen_titles[title] = date
                result.append(r)
            else:
                if date > seen_titles[title]:
                    for i, existing in enumerate(result):
                        if existing.get("title") == title:
                            result[i] = r
                            seen_titles[title] = date
                            break
        
        return result
    
    def run(self):
        """运行爬虫"""
        logger.info("=== 开始抓取赣州市当日招标公告 ===")
        start_time = datetime.now()
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_records = []
        
        # ========== 步骤1: 依次抓取各数据源 ==========
        logger.info("[步骤1] 抓取各数据源...")
        
        for source_name, crawler in self.crawlers.items():
            try:
                logger.info(f"--- 抓取 {source_name} ---")
                
                if source_name == "jxsggzy":
                    records = crawler.crawl_today()
                elif source_name == "ccgp":
                    records = crawler.crawl_today()
                
                # 添加来源标识
                for r in records:
                    r["source"] = source_name
                
                all_records.extend(records)
                self.stats["sources"][source_name] = len(records)
                logger.info(f"  {source_name} 获取 {len(records)} 条")
                
            except Exception as e:
                logger.error(f"  {source_name} 抓取失败: {e}")
                self.stats["sources"][source_name] = 0
        
        self.stats["total_fetched"] = len(all_records)
        logger.info(f"共抓取 {len(all_records)} 条公告")
        
        if not all_records:
            logger.warning("未抓取到任何数据")
            return None
        
        # ========== 步骤2: 内容去重（基于项目名称相似度，跨数据源） ==========
        logger.info("[步骤2] 内容去重（多数据源重复检测）...")
        before_count = len(all_records)
        all_records = deduplicate_by_content(all_records, threshold=0.70)
        after_count = len(all_records)
        logger.info(f"内容去重: {before_count} -> {after_count} 条（过滤 {before_count - after_count} 条重复）")
        self.stats["after_content_dedup"] = after_count
        
        # ========== 步骤3: 标题去重 ==========
        logger.info("[步骤3] 标题去重...")
        before_count = len(all_records)
        all_records = self._deduplicate_by_title(all_records)
        logger.info(f"标题去重: {before_count} -> {len(all_records)} 条")
        
        # ========== 步骤4: 排序（按时间降序） ==========
        logger.info("[步骤4] 排序（按发布时间降序）...")
        all_records.sort(key=lambda x: x.get("publish_date", ""), reverse=True)
        
        # ========== 步骤5: 转换为标准输出格式 ==========
        logger.info("[步骤5] 转换输出格式...")
        announcements = []
        for r in all_records:
            announcements.append({
                "title": r.get("title", ""),
                "publish_date": r.get("webdate", "")[:10] if r.get("webdate") else "",
                "url": r.get("linkurl", ""),
                "content": r.get("content", ""),
                "source": r.get("source", ""),
            })
        
        # ========== 步骤6: 保存结果 ==========
        logger.info("[步骤6] 保存JSON结果...")
        result = {
            "date": today,
            "total_count": len(announcements),
            "sources": self.stats["sources"],
            "announcements": announcements,
        }
        
        result_file = os.path.join(self.output_dir, f"result_{today}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存: {result_file}")
        
        # ========== 完成 ==========
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== 抓取完成，耗时 {elapsed:.1f} 秒 ===")
        logger.info(f"统计: 总抓取={self.stats['total_fetched']}, "
                   f"去重后={len(announcements)}")
        for src, cnt in self.stats["sources"].items():
            logger.info(f"  {src}: {cnt} 条")
        
        return result


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="赣州市招标公告爬虫")
    parser.add_argument("--output", "-o", default="output", help="输出目录")
    
    args = parser.parse_args()
    
    crawler = TenderCrawler(output_dir=args.output)
    result = crawler.run()
    
    if result:
        print(f"\n今日结果 ({result['date']}):")
        print(f"共 {result['total_count']} 条公告（去重后）")
        print(f"来源分布: {result['sources']}")
        print()
        for i, item in enumerate(result['announcements'][:10], 1):
            print(f"{i}. [{item['publish_date']}] [{item['source']}]")
            print(f"   {item['title'][:60]}...")
            print(f"   URL: {item['url'][:60] if item['url'] else '(无)'}")
            print()
        if len(result['announcements']) > 10:
            print(f"... 还有 {len(result['announcements']) - 10} 条")


if __name__ == "__main__":
    main()
