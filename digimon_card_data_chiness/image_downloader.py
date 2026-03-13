"""
数码兽卡牌图片下载模块
支持批量下载、重试机制、进度显示
"""

import os
import re
import time
import requests
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


# 默认图片存储目录
DEFAULT_IMAGE_DIR = "D:\\LLMProject\\dtcg_judger\\card_data\\images\\cn\\raw"


class ImageDownloader:
    """卡牌图片下载器"""
    
    def __init__(self, save_dir: str = DEFAULT_IMAGE_DIR, timeout: int = 30, max_retries: int = 3):
        """
        初始化下载器
        
        Args:
            save_dir: 图片保存目录
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.save_dir = Path(save_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://app.digicamoe.cn/'
        })
        
        # 确保目录存在
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载统计
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def generate_filename(self, card_info: Dict) -> str:
        """
        生成图片文件名
        
        Args:
            card_info: 卡牌信息字典
            
        Returns:
            文件名（含扩展名）
        """
        card_no = card_info.get('card_no', '')
        
        # 清理编号中的特殊字符
        card_no = re.sub(r'[^\w\-]', '_', card_no)
        
        if not card_no:
            # 如果没有编号，使用时间戳
            card_no = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{card_no}.jpg"
    
    def download_single(self, image_url: str, filename: str, overwrite: bool = False) -> bool:
        """
        下载单张图片
        
        Args:
            image_url: 图片 URL
            filename: 保存文件名
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            下载是否成功
        """
        filepath = self.save_dir / filename
        
        # 检查文件是否已存在
        if filepath.exists() and not overwrite:
            print(f"  [SKIP] 已存在：{filename}")
            self.stats['skipped'] += 1
            return True
        
        # 下载
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(image_url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # 写入文件
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  [OK] 下载成功：{filename}")
                self.stats['success'] += 1
                return True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = attempt * 2
                    print(f"  [RETRY] 下载失败，{wait_time}秒后重试 ({attempt}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    print(f"  [FAIL] 下载失败：{filename} - {e}")
                    self.stats['failed'] += 1
                    return False
        
        return False
    
    def download_card(self, card_info: Dict, overwrite: bool = False) -> Dict:
        """
        下载单张卡牌的图片
        
        Args:
            card_info: 卡牌信息字典（需包含 image_url 和 card_no）
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            下载结果字典
        """
        image_url = card_info.get('image_url', '')
        
        if not image_url:
            print(f"  [WARN] 无图片 URL，跳过：{card_info.get('card_no', '未知')}")
            return {
                'success': False,
                'reason': 'no_image_url',
                'card_no': card_info.get('card_no', '')
            }
        
        filename = self.generate_filename(card_info)
        success = self.download_single(image_url, filename, overwrite)
        
        return {
            'success': success,
            'filename': filename,
            'filepath': str(self.save_dir / filename),
            'image_url': image_url,
            'card_no': card_info.get('card_no', '')
        }
    
    def download_batch(self, cards: List[Dict], overwrite: bool = False, delay: float = 0.5) -> List[Dict]:
        """
        批量下载卡牌图片
        
        Args:
            cards: 卡牌信息列表
            overwrite: 是否覆盖已存在的文件
            delay: 下载间隔（秒）
            
        Returns:
            下载结果列表
        """
        results = []
        total = len(cards)
        
        print(f"\n{'='*60}")
        print(f"开始批量下载，共 {total} 张卡牌")
        print(f"保存目录：{self.save_dir}")
        print(f"{'='*60}\n")
        
        for idx, card in enumerate(cards, 1):
            card_no = card.get('card_no', f'#{idx}')
            print(f"[{idx}/{total}] {card_no}", end=" ")
            
            result = self.download_card(card, overwrite)
            results.append(result)
            
            if delay > 0 and idx < total:
                time.sleep(delay)
        
        # 打印统计
        print(f"\n{'='*60}")
        print(f"下载完成！")
        print(f"  成功：{self.stats['success']}")
        print(f"  跳过：{self.stats['skipped']}")
        print(f"  失败：{self.stats['failed']}")
        print(f"{'='*60}\n")
        
        return results
    
    def download_from_database(self, db, limit: Optional[int] = None, overwrite: bool = False) -> List[Dict]:
        """
        从数据库下载所有卡牌图片
        
        Args:
            db: DigimonCardDatabase 对象
            limit: 限制下载数量（None 表示全部）
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            下载结果列表
        """
        cards = db.get_all_cards()
        
        if limit:
            cards = cards[:limit]
        
        # 重置统计
        self.stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        return self.download_batch(cards, overwrite)
    
    def get_stats(self) -> Dict:
        """获取下载统计"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置下载统计"""
        self.stats = {'success': 0, 'failed': 0, 'skipped': 0}


def download_card_image(card_info: Dict, save_dir: str = DEFAULT_IMAGE_DIR) -> Dict:
    """
    便捷函数：下载单张卡牌图片
    
    Args:
        card_info: 卡牌信息字典
        save_dir: 保存目录
        
    Returns:
        下载结果字典
    """
    downloader = ImageDownloader(save_dir=save_dir)
    return downloader.download_card(card_info)


def download_cards_batch(cards: List[Dict], save_dir: str = DEFAULT_IMAGE_DIR, delay: float = 0.5) -> List[Dict]:
    """
    便捷函数：批量下载卡牌图片
    
    Args:
        cards: 卡牌信息列表
        save_dir: 保存目录
        delay: 下载间隔（秒）
        
    Returns:
        下载结果列表
    """
    downloader = ImageDownloader(save_dir=save_dir)
    return downloader.download_batch(cards, delay=delay)


if __name__ == "__main__":
    # 测试示例
    print("数码兽卡牌图片下载器 - 测试模式")
    print("=" * 60)
    
    # 测试数据
    test_cards = [
        {
            'card_no': 'BT25-044',
            'name_cn': '朱诺兽',
            'image_url': 'https://dtcg-wechat.moecard.cn/img/card/12617_19775.MRqPzaYHOV6.jpg~card.jpg'
        },
        {
            'card_no': 'BT25-097',
            'name_cn': '守护者宫殿',
            'image_url': 'https://dtcg-wechat.moecard.cn/img/card/12618_19776.MBwrrI7UuOX.jpg~card.jpg'
        }
    ]
    
    downloader = ImageDownloader()
    results = downloader.download_batch(test_cards, delay=1.0)
    
    print("\n测试结果:")
    for r in results:
        print(f"  {r['card_no']}: {'✓' if r['success'] else '✗'}")
