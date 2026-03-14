"""
日文卡牌爬虫
基于原有 card_data_scraper_JP/scraper.py 重构
"""

import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加原有爬虫路径
ORIGINAL_SCRAPER_PATH = Path(__file__).parent.parent.parent / "card_data_scraper_JP"
sys.path.insert(0, str(ORIGINAL_SCRAPER_PATH))

from scraper import CardScraper as OriginalCardScraper


class JapaneseCardScraper:
    """
    日文卡牌爬虫包装类
    复用原有爬虫代码，提供统一接口
    """
    
    def __init__(self, headless=True, delay=0.5, output_path=None):
        """
        初始化爬虫
        
        Args:
            headless: 是否无头模式
            delay: 爬取延迟（秒）
            output_path: 输出路径
        """
        self.headless = headless
        self.delay = delay
        self.output_path = Path(output_path) if output_path else ORIGINAL_SCRAPER_PATH.parent / "digimon_card_data"
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # 使用原有爬虫
        self.original_scraper = OriginalCardScraper(
            headless=headless,
            output_dir=str(self.output_path)
        )
        
        print(f"✓ 日文卡牌爬虫已初始化")
        print(f"  输出路径：{self.output_path}")
        print(f"  无头模式：{headless}")
        print(f"  延迟：{delay}s")
    
    def scrape_all_packs(self):
        """爬取所有卡包"""
        print("\n开始爬取所有卡包...")
        
        try:
            # 调用原有爬虫的 main 方法
            self.original_scraper.main()
            print("✓ 所有卡包爬取完成")
        except Exception as e:
            print(f"✗ 爬取失败：{e}")
            raise
    
    def scrape_pack(self, pack_id):
        """
        爬取指定卡包
        
        Args:
            pack_id: 卡包 ID（如 "503035"）
        """
        print(f"\n爬取卡包：{pack_id}")
        
        try:
            # 调用原有爬虫方法
            self.original_scraper.scrape_all_cards(pack_id)
            print(f"✓ 卡包 {pack_id} 爬取完成")
        except Exception as e:
            print(f"✗ 卡包 {pack_id} 爬取失败：{e}")
            raise
    
    def close(self):
        """关闭浏览器"""
        try:
            self.original_scraper.close()
            print("✓ 浏览器已关闭")
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 直接使用原有爬虫（如果独立运行）
if __name__ == "__main__":
    scraper = JapaneseCardScraper(headless=False)
    try:
        scraper.scrape_all_packs()
    finally:
        scraper.close()
