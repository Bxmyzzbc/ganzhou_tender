"""
去重模块
使用历史记录避免重复抓取
"""

import json
import os
import logging
from typing import List, Dict, Set
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Deduplicator:
    """去重器"""
    
    def __init__(self, history_file: str = "history.json"):
        self.history_file = history_file
        self.seen_ids: Set[str] = set()
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.seen_ids = set(data.get("seen_ids", []))
                    logger.info(f"加载历史记录 {len(self.seen_ids)} 条")
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}")
                self.seen_ids = set()
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump({
                    "seen_ids": list(self.seen_ids),
                    "updated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def is_seen(self, record: Dict) -> bool:
        """
        判断记录是否已见过
        
        使用 infoid 或 linkurl 作为唯一标识
        """
        record_id = record.get("infoid") or record.get("linkurl", "")
        return record_id in self.seen_ids
    
    def add_seen(self, record: Dict):
        """标记为已见"""
        record_id = record.get("infoid") or record.get("linkurl", "")
        if record_id:
            self.seen_ids.add(record_id)
    
    def filter_new(self, records: List[Dict]) -> List[Dict]:
        """
        过滤出新增的记录
        
        Returns:
            [new_records, old_records] - 新记录列表和已存在记录列表
        """
        new_records = []
        old_records = []
        
        for r in records:
            if self.is_seen(r):
                old_records.append(r)
            else:
                new_records.append(r)
                self.add_seen(r)
        
        if new_records:
            self._save_history()
            logger.info(f"新增 {len(new_records)} 条，过滤 {len(old_records)} 条重复")
        
        return new_records


def test():
    """测试去重"""
    dedup = Deduplicator("test_history.json")
    
    # 模拟记录
    records = [
        {"infoid": "abc123", "title": "测试1"},
        {"infoid": "def456", "title": "测试2"},
        {"infoid": "abc123", "title": "测试1重复"},  # 重复
    ]
    
    new_records, old_records = dedup.filter_new(records)
    
    print(f"新记录: {len(new_records)}")
    print(f"重复记录: {len(old_records)}")
    
    for r in new_records:
        print(f"  新: {r['title']}")
    for r in old_records:
        print(f"  旧: {r['title']}")
    
    # 清理测试文件
    if os.path.exists("test_history.json"):
        os.remove("test_history.json")


if __name__ == "__main__":
    test()
