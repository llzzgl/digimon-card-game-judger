"""
DTCG 卡牌图片批量下载工具 v2
从日文官网爬取所有卡包图片（修复版 - 适配新网站结构）
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
    # 使用不带过滤参数的 URL
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
    
    def get_all_cards(self) -> List[Dict]:
        """获取所有卡牌（直接从主页面）"""
        logger.info("获取所有卡牌列表...")
        
        cards = []
        
        # 访问不带过滤的页面
        self.driver.get(self.CARDLIST_URL)
        time.sleep(5)
        
        # 等待页面加载完成
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[class*='card']"))
        )
        
        # 查找所有卡牌元素 - 使用更通用的选择器
        card_elements = self.driver.find_elements(By.CSS_SELECTOR, "li[class*='card']")
        logger.info(f"找到 {len(card_elements)} 张卡牌元素")
        
        for i, card_elem in enumerate(card_elements, 1):
            try:
                card_info = self.extract_card_info(card_elem)
                if card_info and card_info.get("image_url"):
                    cards.append(card_info)
                    
                if i % 500 == 0:
                    logger.info(f"  已处理 {i}/{len(card_elements)} 张卡牌...")
                    
            except Exception as e:
                logger.warning(f"  提取卡牌失败 ({i}): {e}")
                self.stats["errors"] += 1
        
        self.stats["cards_found"] = len(cards)
        logger.info(f"成功提取 {len(cards)} 张卡牌信息")
        return cards
    
    def extract_card_info(self, card_elem) -> Dict:
        """从卡牌元素提取信息"""
        card_info = {
            "pack_name": "",
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
            if href:
                match = re.search(r'card_no=(\d+)', href)
                if match:
                    card_info["card_no"] = match.group(1)
            
            # 查找图片
            try:
                img_elem = card_elem.find_element(By.TAG_NAME, "img")
                card_info["image_url"] = img_elem.get_attribute("src")
                
                # 如果是相对路径，转换为绝对路径
                if card_info["image_url"] and not card_info["image_url"].startswith('http'):
                    card_info["image_url"] = self.BASE_URL + card_info["image_url"]
            except:
                pass
            
            # 提取稀有度（从 class）
            card_class = card_elem.get_attribute("class") or ""
            card_info["rarity"] = card_class
            
            # 尝试提取卡包名称（从 data 属性或父级）
            try:
                parent = card_elem.find_element(By.XPATH, "..")
                # 尝试从各种属性获取卡包信息
                for attr in ['data-set', 'data-series', 'class']:
                    val = parent.get_attribute(attr)
                    if val:
                        card_info["pack_name"] = val
                        break
            except:
                pass
            
            # 如果还是没有卡包名，用编号前缀
            if not card_info["pack_name"] and card_info["card_no"]:
                # 假设编号格式如 "AD1-001"
                match = re.match(r'([A-Z]+[\d]*-)', card_info["card_no"])
                if match:
                    card_info["pack_name"] = match.group(1)
            
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
            safe_pack = re.sub(r'[^\w\s-]', '', str(pack_name)).strip()[:20]
            safe_no = re.sub(r'[^\w\s-]', '', str(card_no)).strip()[:20]
            filename = f"{safe_pack}_{safe_no}.jpg"
            output_path = self.output_dir / filename
            
            # 检查是否已存在
            if output_path.exists():
                self.stats["images_skipped"] += 1
                return True
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.BASE_URL
            }
            response = requests.get(image_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.stats["images_downloaded"] += 1
            if self.stats["images_downloaded"] % 100 == 0:
                logger.info(f"  ✓ 已下载 {self.stats['images_downloaded']} 张图片...")
            
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {card_info.get('card_no', 'unknown')}: {e}")
            self.stats["errors"] += 1
            return False
    
    def run(self):
        """执行爬取任务"""
        logger.info("=" * 60)
        logger.info("DTCG 卡牌图片批量下载开始")
        logger.info("=" * 60)
        
        # 获取所有卡牌
        cards = self.get_all_cards()
        
        if not cards:
            logger.error("没有找到任何卡牌！")
            self.print_stats()
            return self.stats
        
        # 下载所有图片
        logger.info(f"\n开始下载 {len(cards)} 张图片...")
        for i, card in enumerate(cards, 1):
            self.download_image(card)
            
            # 限速
            if i % 10 == 0:
                time.sleep(1)
            
            # 每 100 张报告进度
            if i % 100 == 0:
                logger.info(f"进度：{i}/{len(cards)} ({100*i//len(cards)}%)")
        
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
    print("DTCG 卡牌图片批量下载工具 v2")
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
