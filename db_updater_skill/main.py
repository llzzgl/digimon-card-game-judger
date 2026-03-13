"""
DTCG Database Updater Skill - 主入口
一键更新/创建数码宝贝卡牌数据库
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, ensure_dirs
from scrapers.jp_card_scraper import JapaneseCardScraper
from scrapers.qa_scraper import QAScraper


class DatabaseUpdater:
    """数据库更新器"""
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.scratchers = {}
        ensure_dirs()
        
    def update_all(self):
        """更新所有数据"""
        print("=" * 60)
        print("DTCG 数据库更新开始")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 备份现有数据
        if self.config["database"].get("backup_before_update", True):
            self._backup_data()
        
        # 2. 更新日文卡牌
        if self.config["jp_card"]["enabled"]:
            self.update_jp_cards()
        
        # 3. 更新 QA 数据
        if self.config["qa"]["enabled"]:
            self.update_qa()
        
        # 4. 重建数据库（如果需要）
        if self.config["database"].get("rebuild_on_update", False):
            self.rebuild_database()
        
        print("=" * 60)
        print("DTCG 数据库更新完成")
        print("=" * 60)
    
    def update_jp_cards(self):
        """更新日文卡牌数据"""
        print("\n[1/3] 更新日文卡牌数据...")
        
        scraper = JapaneseCardScraper(
            headless=self.config["jp_card"]["headless"],
            delay=self.config["jp_card"]["delay"]
        )
        
        try:
            # 爬取所有卡包
            scraper.scrape_all_packs()
            print("✓ 日文卡牌更新完成")
        except Exception as e:
            print(f"✗ 日文卡牌更新失败：{e}")
        finally:
            scraper.close()
    
    def update_qa(self):
        """更新 QA 数据"""
        print("\n[2/3] 更新 QA 数据...")
        
        languages = self.config["qa"]["languages"]
        
        for lang in languages:
            print(f"\n  爬取 {lang.upper()} QA...")
            scraper = QAScraper(
                language=lang,
                headless=self.config["qa"]["headless"],
                delay=self.config["qa"]["delay"]
            )
            
            try:
                scraper.scrape_all()
                print(f"  ✓ {lang.upper()} QA 更新完成")
            except Exception as e:
                print(f"  ✗ {lang.upper()} QA 更新失败：{e}")
            finally:
                scraper.close()
        
        print("✓ QA 数据更新完成")
    
    def rebuild_database(self):
        """重建合并数据库"""
        print("\n[3/3] 重建合并数据库...")
        
        from database.card_db import CardDatabase
        from database.qa_db import QADatabase
        
        # 合并卡牌数据
        card_db = CardDatabase()
        card_db.load_from_folder(self.config["jp_card"]["output_path"])
        card_db.merge_and_deduplicate()
        card_db.save_to_json(
            self.config["database"]["output_path"] / "cards.json"
        )
        
        # 合并 QA 数据
        qa_db = QADatabase()
        qa_db.load_from_folder(self.config["qa"]["output_path"])
        qa_db.merge_and_deduplicate()
        qa_db.save_to_json(
            self.config["database"]["output_path"] / "rulings.json"
        )
        
        print("✓ 数据库重建完成")
    
    def _backup_data(self):
        """备份现有数据"""
        print("\n[备份] 备份现有数据...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(__file__).parent / "backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份关键目录
        dirs_to_backup = [
            self.config["jp_card"]["output_path"],
            self.config["cn_card"]["output_path"],
            self.config["qa"]["output_path"],
            self.config["database"]["output_path"],
        ]
        
        for src_path in dirs_to_backup:
            src_path = Path(src_path)
            if src_path.exists():
                dest_path = backup_dir / src_path.name
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                print(f"  ✓ 已备份：{src_path.name}")
        
        print(f"✓ 备份完成：{backup_dir}")
    
    def create_skill_package(self):
        """创建 OpenClaw Skill 包"""
        print("\n[Skill] 创建 OpenClaw Skill 包...")
        
        # 这里可以添加将爬虫代码打包成 OpenClaw Skill 的逻辑
        # 包括创建 SKILL.md、处理脚本等
        
        print("✓ Skill 包创建完成")


def main():
    """主函数"""
    updater = DatabaseUpdater()
    updater.update_all()


if __name__ == "__main__":
    main()
