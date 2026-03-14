"""
DTCG 卡牌图片批量下载工具 v4
完整版 - 遍历所有卡包系列下载所有卡牌图片
"""

import sys
import logging
from pathlib import Path
import time
import re
import os
from typing import List, Dict

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import requests
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.error(f"Selenium 未安装：{e}")


class CardImageScraper:
    """卡牌图片爬虫"""
    
    BASE_URL = "https://digimoncard.com"
    CARDLIST_URL = f"{BASE_URL}/cards/"
    
    # 所有卡包系列 ID (从网页中提取)
    # BT 系列 (主系列)
    BT_SERIES = [f"5030{i:02d}" for i in range(1, 38)]  # BT-01 to BT-24
    # EX 系列 (额外系列)
    EX_SERIES = [f"5030{i:02d}" for i in range(7, 37)]  # EX-01 to EX-11
    # ST 系列 (起始卡组)
    ST_SERIES = [f"5031{i:02d}" for i in range(1, 23)]  # ST-1 to ST-22
    # LM 系列 (限量版)
    LM_SERIES = [f"5032{i:02d}" for i in range(1, 7)]   # LM-01 to LM-06
    
    # 合并所有系列
    ALL_SERIES = BT_SERIES + EX_SERIES + ST_SERIES + LM_SERIES
    
    def __init__(self, headless: bool = True, output_dir: str = "card_data/images/jp/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "packs_processed": 0,
            "cards_found": 0,
            "images_downloaded": 0,
            "images_skipped": 0,
            "errors": 0
        }
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver 初始化完成")
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def get_cards_from_category(self, category_id: str) -> List[Dict]:
        """从指定分类获取卡牌"""
        cards = []
        
        try:
            url = f"{self.CARDLIST_URL}?search=true&category={category_id}"
            self.driver.get(url)
            time.sleep(3)
            
            # 等待卡牌加载
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.card_img"))
                )
            except:
                logger.warning(f"  分类 {category_id} 没有卡牌或加载超时")
                return cards
            
            # 查找所有卡牌图片链接
            card_links = self.driver.find_elements(By.CSS_SELECTOR, "a.card_img")
            
            for link in card_links:
                try:
                    img = link.find_element(By.TAG_NAME, "img")
                    img_src = img.get_attribute("src") or img.get_attribute("data-src")
                    
                    if img_src and 'noimage' not in img_src:
                        # 处理相对路径
                        if img_src.startswith("../"):
                            img_src = self.BASE_URL + "/cards/" + img_src[3:]
                        elif img_src.startswith("/"):
                            img_src = self.BASE_URL + img_src
                        
                        # 提取卡牌编号
                        card_no = "unknown"
                        match = re.search(r'/card/([^.]+)\.png', img_src)
                        if match:
                            card_no = match.group(1)
                        
                        cards.append({
                            "card_no": card_no,
                            "image_url": img_src,
                            "filename": f"{card_no}.jpg"
                        })
                except Exception as e:
                    logger.warning(f"    提取卡牌失败：{e}")
                    self.stats["errors"] += 1
            
            self.stats["cards_found"] += len(cards)
            logger.info(f"  找到 {len(cards)} 张卡牌")
            
        except Exception as e:
            logger.error(f"  获取分类 {category_id} 失败：{e}")
            self.stats["errors"] += 1
        
        return cards
    
    def download_image(self, card_info: Dict) -> bool:
        """下载卡牌图片"""
        try:
            image_url = card_info.get("image_url")
            if not image_url:
                return False
            
            filename = card_info.get("filename", "unknown.jpg")
            output_path = self.output_dir / filename
            
            # 检查是否已存在
            if output_path.exists():
                self.stats["images_skipped"] += 1
                return True
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.BASE_URL
            }
            response = requests.get(image_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats["images_downloaded"] += 1
            return True
            
        except Exception as e:
            logger.error(f"  下载失败 {card_info.get('card_no', 'unknown')}: {e}")
            self.stats["errors"] += 1
            return False
    
    def run(self):
        """执行爬取任务"""
        logger.info("=" * 60)
        logger.info("DTCG 卡牌图片批量下载开始")
        logger.info(f"总共 {len(self.ALL_SERIES)} 个卡包系列")
        logger.info("=" * 60)
        
        all_cards = []
        
        # 遍历所有系列
        for i, category_id in enumerate(self.ALL_SERIES, 1):
            logger.info(f"\n[{i}/{len(self.ALL_SERIES)}] 处理系列 {category_id}...")
            cards = self.get_cards_from_category(category_id)
            all_cards.extend(cards)
            self.stats["packs_processed"] += 1
            
            # 限速
            time.sleep(1)
        
        logger.info(f"\n总共找到 {len(all_cards)} 张卡牌")
        
        # 去重
        unique_cards = {}
        for card in all_cards:
            if card["card_no"] not in unique_cards:
                unique_cards[card["card_no"]] = card
        
        all_cards = list(unique_cards.values())
        logger.info(f"去重后 {len(all_cards)} 张卡牌")
        
        # 下载所有图片
        if all_cards:
            logger.info(f"\n开始下载 {len(all_cards)} 张图片...")
            for i, card in enumerate(all_cards, 1):
                self.download_image(card)
                
                # 限速
                if i % 10 == 0:
                    time.sleep(0.5)
                
                # 报告进度
                if i % 100 == 0:
                    logger.info(f"进度：{i}/{len(all_cards)} ({100*i//len(all_cards)}%)")
        
        # 输出统计
        self.print_stats()
        
        return self.stats
    
    def print_stats(self):
        """打印统计信息"""
        print()
        print("=" * 60)
        print("爬取完成")
        print("=" * 60)
        print(f"处理卡包：{self.stats['packs_processed']} 个")
        print(f"发现卡牌：{self.stats['cards_found']} 张")
        print(f"下载图片：{self.stats['images_downloaded']} 张")
        print(f"跳过图片：{self.stats['images_skipped']} 张")
        print(f"错误次数：{self.stats['errors']} 次")
        print(f"输出目录：{self.output_dir}")


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 卡牌图片批量下载工具 v4")
    print("=" * 60)
    print()
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium 未安装")
        print("   请运行：pip install selenium webdriver-manager")
        return None
    
    scraper = CardImageScraper(headless=True)
    
    try:
        stats = scraper.run()
        return stats
    finally:
        scraper.close()


if __name__ == "__main__":
    stats = main()
    sys.exit(0 if stats and (stats["images_downloaded"] > 0 or stats["images_skipped"] > 0) else 1)
