"""
日文卡牌图片下载器
来源：https://digimoncard.com
"""

import requests
import logging
from pathlib import Path
from typing import List, Optional
import time

logger = logging.getLogger(__name__)


class JapaneseImageDownloader:
    """日文卡牌图片下载器"""
    
    def __init__(self, output_dir: str, version: str = "02"):
        """
        初始化下载器
        
        Args:
            output_dir: 输出目录路径
            version: 图片版本号（默认"02"）
        """
        self.output_dir = Path(output_dir)
        self.version = version
        self.base_url = "https://digimoncard.com/images/cardlist/card/"
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"日文图片下载器初始化完成 - 输出目录：{self.output_dir}")
    
    def generate_card_numbers(self, series: str, count: int) -> List[str]:
        """
        生成卡牌编号列表
        
        Args:
            series: 系列代码（如"EX11"）
            count: 数量
            
        Returns:
            卡牌编号列表（如["EX11-001", "EX11-002", ...]）
        """
        cards = []
        for i in range(1, count + 1):
            card_no = f"{series}-{i:03d}"
            cards.append(card_no)
        return cards
    
    def build_image_url(self, card_number: str) -> str:
        """
        构建图片 URL
        
        Args:
            card_number: 卡牌编号（如"EX11-001"）
            
        Returns:
            完整的图片 URL
        """
        return f"{self.base_url}{card_number}.png?{self.version}"
    
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
                
                # 写入文件
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"下载成功：{output_path.name}")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 重试前等待 2 秒
                else:
                    logger.error(f"下载最终失败：{url}")
                    return False
        
        return False
    
    def download_cards(self, series: str, count: int = 10, skip_existing: bool = True) -> dict:
        """
        批量下载卡牌图片
        
        Args:
            series: 系列代码
            count: 下载数量
            skip_existing: 是否跳过已存在的文件
            
        Returns:
            下载统计信息
        """
        stats = {
            "total": count,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "files": []
        }
        
        logger.info(f"开始下载 {series} 系列，目标数量：{count}")
        
        card_numbers = self.generate_card_numbers(series, count)
        
        for card_no in card_numbers:
            url = self.build_image_url(card_no)
            filename = f"{card_no}_v{self.version}.png"
            output_path = self.output_dir / filename
            
            # 检查是否已存在
            if skip_existing and output_path.exists():
                logger.info(f"跳过已存在的文件：{filename}")
                stats["skipped"] += 1
                continue
            
            # 下载图片
            if self.download_image(url, output_path):
                stats["success"] += 1
                stats["files"].append(filename)
            else:
                stats["failed"] += 1
        
        logger.info(f"下载完成 - 成功：{stats['success']}, 失败：{stats['failed']}, 跳过：{stats['skipped']}")
        return stats
