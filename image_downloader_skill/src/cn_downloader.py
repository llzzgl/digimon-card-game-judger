"""
中文卡牌图片下载器
来源：https://app.digicamoe.cn
需要使用 Selenium 动态加载页面
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time
import re

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
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium 未安装，中文图片下载功能将不可用")


class ChineseImageDownloader:
    """中文卡牌图片下载器"""
    
    def __init__(self, output_dir: str):
        """
        初始化下载器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.driver = None
        self.image_cdn = "https://dtcg-wechat.moecard.cn/img/card/"
        
        logger.info(f"中文图片下载器初始化完成 - 输出目录：{self.output_dir}")
    
    def setup_driver(self):
        """设置 Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium 未安装，请先安装：pip install selenium webdriver-manager")
        
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver 初始化完成")
    
    def close_driver(self):
        """关闭 WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome WebDriver 已关闭")
    
    def extract_image_url_from_page(self, card_url: str) -> Optional[str]:
        """
        从卡牌详情页提取图片 URL
        
        Args:
            card_url: 卡牌详情页 URL
            
        Returns:
            图片 URL，如果提取失败返回 None
        """
        try:
            self.setup_driver()
            self.driver.get(card_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.lazyLoad"))
            )
            
            # 查找带有 lazyLoad 类的图片
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img.lazyLoad")
            
            for img in img_elements:
                src = img.get_attribute("src")
                if src and self.image_cdn in src:
                    logger.info(f"找到图片 URL: {src}")
                    return src
            
            # 尝试通过 title 属性查找
            try:
                img_element = self.driver.find_element(By.XPATH, "//img[contains(@title, '卡图')]")
                src = img_element.get_attribute("src")
                if src:
                    logger.info(f"通过 title 属性找到图片 URL: {src}")
                    return src
            except:
                pass
            
            logger.warning(f"未找到图片 URL: {card_url}")
            return None
            
        except Exception as e:
            logger.error(f"提取图片 URL 失败：{e}")
            return None
    
    def download_image(self, url: str, output_path: Path, max_retries: int = 3) -> bool:
        """
        下载单张图片
        
        Args:
            url: 图片 URL
            output_path: 输出文件路径
            max_retries: 最大重试次数
            
        Returns:
            下载是否成功
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"下载图片：{url} (尝试 {attempt + 1}/{max_retries})")
                
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"下载成功：{output_path.name}")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error(f"下载最终失败：{url}")
                    return False
        
        return False
    
    def download_cards_from_urls(self, card_urls: List[str], output_prefix: str = "") -> dict:
        """
        从 URL 列表批量下载卡牌图片
        
        Args:
            card_urls: 卡牌详情页 URL 列表
            output_prefix: 输出文件名前缀
            
        Returns:
            下载统计信息
        """
        stats = {
            "total": len(card_urls),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "files": []
        }
        
        try:
            for i, card_url in enumerate(card_urls, 1):
                logger.info(f"处理卡牌 {i}/{len(card_urls)}: {card_url}")
                
                # 提取图片 URL
                image_url = self.extract_image_url_from_page(card_url)
                if not image_url:
                    stats["failed"] += 1
                    continue
                
                # 生成文件名
                # 从 URL 中提取卡牌编号
                match = re.search(r'/Cards/([^/]+)/([^/]+)', card_url)
                if match:
                    series = match.group(1)
                    card_no = match.group(2)
                    filename = f"{output_prefix}{series}-{card_no}.jpg"
                else:
                    filename = f"{output_prefix}card_{i:03d}.jpg"
                
                output_path = self.output_dir / filename
                
                # 检查是否已存在
                if output_path.exists():
                    logger.info(f"跳过已存在的文件：{filename}")
                    stats["skipped"] += 1
                    continue
                
                # 下载图片
                if self.download_image(image_url, output_path):
                    stats["success"] += 1
                    stats["files"].append(filename)
                else:
                    stats["failed"] += 1
                
                # 避免请求过快
                time.sleep(1)
        
        finally:
            self.close_driver()
        
        logger.info(f"下载完成 - 成功：{stats['success']}, 失败：{stats['failed']}, 跳过：{stats['skipped']}")
        return stats
