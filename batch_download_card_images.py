"""
DTCG 卡牌图片批量下载工具
从日文官网爬取所有卡包图片（含异画版本）
"""

import sys
import logging
from pathlib import Path
import time
import json
import re
import os
from typing import List, Dict

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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
    
    def get_all_pack_urls(self) -> List[Dict]:
        """获取所有卡包 URL"""
        logger.info("获取所有卡包列表...")
        
        packs = []
        self.driver.get(self.CARDLIST_URL)
        time.sleep(5)
        
        # 查找所有卡包链接
        pack_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/cards/list/']")
        
        for link in pack_links:
            href = link.get_attribute("href")
            text = link.text.strip()
            if href and text:
                packs.append({
                    "pack_name": text,
                    "pack_url": href
                })
        
        logger.info(f"找到 {len(packs)} 个卡包")
        return packs
    
    def scrape_pack_images(self, pack_name: str, pack_url: str) -> List[Dict]:
        """从卡包页面爬取所有卡牌图片"""
        logger.info(f"\n爬取卡包：{pack_name}")
        
        cards = []
        
        try:
            self.driver.get(pack_url)
            time.sleep(4)
            
            # 查找所有卡牌元素
            card_elements = self.driver.find_elements(By.CSS_SELECTOR, ".card_list li, .cardlist li")
            logger.info(f"  找到 {len(card_elements)} 张卡牌")
            
            for i, card_elem in enumerate(card_elements, 1):
                try:
                    # 提取卡牌信息
                    card_info = self.extract_card_info(card_elem, pack_name)
                    if card_info:
                        cards.append(card_info)
                except Exception as e:
                    logger.warning(f"  提取卡牌失败：{e}")
                    self.stats["errors"] += 1
            
            self.stats["packs_processed"] += 1
            self.stats["cards_found"] += len(cards)
            
        except Exception as e:
            logger.error(f"爬取卡包失败：{e}")
            self.stats["errors"] += 1
        
        return cards
    
    def extract_card_info(self, card_elem, pack_name: str) -> Dict:
        """从卡牌元素提取信息"""
        card_info = {
            "pack_name": pack_name,
            "card_no": "",
            "card_name": "",
            "rarity": "",
            "image_url": "",
            "card_url": ""
        }
        
        try:
            # 查找卡牌链接
            link_elem = card_elem.find_element(By.TAG_NAME, "a")
            card_info["card_url"] = link_elem.get_attribute("href")
            
            # 提取卡牌编号
            href = card_info["card_url"]
            match = re.search(r'card_no=(\d+)', href)
            if match:
                card_info["card_no"] = match.group(1)
            
            # 查找图片
            img_elem = card_elem.find_element(By.TAG_NAME, "img")
            card_info["image_url"] = img_elem.get_attribute("src")
            
            # 提取稀有度（从 class 或其他属性）
            card_info["rarity"] = card_elem.get_attribute("class") or ""
            
        except Exception as e:
            logger.warning(f"提取信息失败：{e}")
        
        return card_info
    
    def download_image(self, card_info: Dict) -> bool:
        """下载卡牌图片"""
        try:
            image_url = card_info.get("image_url")
            if not image_url:
                return False
            
            # 生成文件名
            card_no = card_info.get("card_no", "unknown")
            pack_name = card_info.get("pack_name", "unknown")
            
            # 清理文件名
            safe_pack = re.sub(r'[^\w\s-]', '', pack_name).strip()[:20]
            filename = f"{safe_pack}_{card_no}.jpg"
            output_path = self.output_dir / filename
            
            # 检查是否已存在
            if output_path.exists():
                self.stats["images_skipped"] += 1
                return True
            
            # 下载图片
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats["images_downloaded"] += 1
            logger.info(f"  ✓ 下载：{filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"下载失败：{e}")
            self.stats["errors"] += 1
            return False
    
    def run(self, max_packs: int = None):
        """执行爬取任务"""
        logger.info("=" * 60)
        logger.info("DTCG 卡牌图片批量下载开始")
        logger.info("=" * 60)
        
        # 获取所有卡包
        packs = self.get_all_pack_urls()
        
        if max_packs:
            packs = packs[:max_packs]
            logger.info(f"限制爬取前 {max_packs} 个卡包")
        
        # 逐个爬取卡包
        for pack in packs:
            cards = self.scrape_pack_images(pack["pack_name"], pack["pack_url"])
            
            # 下载图片
            for card in cards:
                self.download_image(card)
            
            # 限速
            time.sleep(2)
        
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
    print("DTCG 卡牌图片批量下载工具")
    print("=" * 60)
    print()
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium 未安装")
        print("   请运行：pip install selenium webdriver-manager")
        return None
    
    scraper = CardImageScraper(headless=True)
    
    try:
        # 执行爬取（不限制卡包数量）
        stats = scraper.run(max_packs=None)
        return stats
    finally:
        scraper.close()


if __name__ == "__main__":
    stats = main()
    sys.exit(0 if stats and stats["images_downloaded"] > 0 else 1)
