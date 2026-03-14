"""
QA 爬虫
基于原有 card_game_QA_manger/scraper_jp_official.py 重构
"""

import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加原有爬虫路径
ORIGINAL_SCRAPER_PATH = Path(__file__).parent.parent.parent / "card_game_judge" / "card_game_QA_manger"
sys.path.insert(0, str(ORIGINAL_SCRAPER_PATH))

from scraper_jp_official import JapaneseOfficialQAScraper as OriginalQAScraper


class QAScraper:
    """
    QA 爬虫包装类
    复用原有爬虫代码，提供统一接口
    """
    
    def __init__(self, language="jp", headless=True, delay=1.0, output_path=None):
        """
        初始化爬虫
        
        Args:
            language: 语言（jp: 日文，cn: 中文）
            headless: 是否无头模式
            delay: 爬取延迟（秒）
            output_path: 输出路径
        """
        self.language = language
        self.headless = headless
        self.delay = delay
        self.output_path = Path(output_path) if output_path else ORIGINAL_SCRAPER_PATH
        
        if self.language == "jp":
            self.output_file = self.output_path / "official_qa_jp.json"
        else:
            self.output_file = self.output_path / "official_qa_cn.json"
        
        # 使用原有爬虫
        self.original_scraper = OriginalQAScraper(
            headless=headless,
            output_file=str(self.output_file)
        )
        
        print(f"✓ QA 爬虫已初始化 ({language.upper()})")
        print(f"  输出文件：{self.output_file}")
        print(f"  无头模式：{headless}")
        print(f"  延迟：{delay}s")
    
    def scrape_all(self):
        """爬取所有 QA"""
        print(f"\n开始爬取 {self.language.upper()} QA...")
        
        try:
            # 调用原有爬虫的 main 方法
            self.original_scraper.main()
            print(f"✓ {self.language.upper()} QA 爬取完成")
        except Exception as e:
            print(f"✗ 爬取失败：{e}")
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
    scraper = QAScraper(language="jp", headless=False)
    try:
        scraper.scrape_all()
    finally:
        scraper.close()
