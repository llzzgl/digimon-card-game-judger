"""
数码宝贝卡牌图片下载模块
用于下载和管理卡牌图片
"""
import os
import re
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


class ImageDownloader:
    """卡牌图片下载器"""
    
    # 图片存储基础路径
    BASE_IMAGE_DIR = r"D:\LLMProject\dtcg_judger\card_data\images\jp"
    
    # 请求配置
    DEFAULT_TIMEOUT = 30  # 秒
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 1  # 重试延迟（秒）
    
    # 请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
        "Referer": "https://digimoncard.com/"
    }
    
    # 无效图片 URL 模式
    NOIMAGE_PATTERNS = [
        "noimage.png",
        "no_image.png",
        "placeholder.png",
        "blank.png"
    ]
    
    def __init__(self, output_dir: str = None, create_dirs: bool = True):
        """
        初始化图片下载器
        
        Args:
            output_dir: 图片输出目录（默认使用 BASE_IMAGE_DIR）
            create_dirs: 是否自动创建目录结构
        """
        self.output_dir = output_dir or self.BASE_IMAGE_DIR
        self.raw_dir = os.path.join(self.output_dir, "raw")
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        # 创建会话用于保持连接
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        if create_dirs:
            self._create_directories()
        
        # 下载统计
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "bytes_downloaded": 0
        }
    
    def _create_directories(self):
        """创建必要的目录结构"""
        os.makedirs(self.raw_dir, exist_ok=True)
        print(f"[OK] 图片存储目录：{self.raw_dir}")
    
    def is_valid_image_url(self, url: str) -> bool:
        """
        检查 URL 是否是有效的图片地址
        
        Args:
            url: 图片 URL
            
        Returns:
            True 如果是有效图片 URL，否则 False
        """
        if not url:
            return False
        
        # 检查是否是无图占位符
        url_lower = url.lower()
        for pattern in self.NOIMAGE_PATTERNS:
            if pattern in url_lower:
                return False
        
        # 检查是否是 http/https URL
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        
        return True
    
    def extract_card_no_from_url(self, url: str) -> Optional[str]:
        """
        从图片 URL 中提取卡牌编号
        
        Args:
            url: 图片 URL
            
        Returns:
            卡牌编号（如 EX11-001），无法提取则返回 None
        """
        if not url:
            return None
        
        # 匹配格式：EX11-001.png, BT-24-001.png, ST18-001.png 等
        match = re.search(r'/([A-Z]{2,3}-?\d{2,3}(?:-\d{3})?)\.png', url)
        if match:
            return match.group(1)
        
        # 备用模式：匹配更广泛的卡牌编号格式
        match = re.search(r'/([A-Z]{2,4}[-/]?\d{2,4})\.png', url)
        if match:
            return match.group(1).replace('/', '-')
        
        return None
    
    def generate_filename(self, card_no: str, url: str, pack_id: str = None) -> str:
        """
        生成图片文件名
        
        Args:
            card_no: 卡牌编号
            url: 图片 URL
            pack_id: 卡包 ID（可选）
            
        Returns:
            文件名（含扩展名）
        """
        # 从 URL 提取版本参数（用于缓存控制）
        version = ""
        if "?" in url:
            version_match = re.search(r'\?(\d+)', url)
            if version_match:
                version = f"_v{version_match.group(1)}"
        
        # 生成文件名格式：{PACK_ID}_{CARD_NO}.png 或 {CARD_NO}.png
        if pack_id:
            # 清理 pack_id 中的特殊字符
            safe_pack_id = re.sub(r'[^A-Z0-9]', '', pack_id.upper())
            filename = f"{safe_pack_id}_{card_no}{version}.png"
        else:
            filename = f"{card_no}{version}.png"
        
        return filename
    
    def download_image(self, url: str, card_no: str = None, pack_id: str = None, 
                      save_path: str = None) -> Tuple[bool, str]:
        """
        下载单张图片
        
        Args:
            url: 图片 URL
            card_no: 卡牌编号（可选，如果为 None 则从 URL 提取）
            pack_id: 卡包 ID（可选，用于文件名）
            save_path: 自定义保存路径（可选，如果为 None 则使用默认路径）
            
        Returns:
            (success: bool, message: str)
        """
        self.stats["total"] += 1
        
        # 验证 URL
        if not self.is_valid_image_url(url):
            self.stats["skipped"] += 1
            return False, f"无效的图片 URL: {url}"
        
        # 提取卡牌编号
        if not card_no:
            card_no = self.extract_card_no_from_url(url)
            if not card_no:
                self.stats["failed"] += 1
                return False, f"无法从 URL 提取卡牌编号：{url}"
        
        # 确定保存路径
        if save_path:
            filepath = save_path
        else:
            filename = self.generate_filename(card_no, url, pack_id)
            filepath = os.path.join(self.raw_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 0:
                self.stats["skipped"] += 1
                return True, f"文件已存在，跳过：{filepath} ({file_size} bytes)"
        
        # 下载图片（带重试）
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT, stream=True)
                response.raise_for_status()
                
                # 检查 Content-Type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    self.stats["failed"] += 1
                    return False, f"非图片内容类型：{content_type}"
                
                # 保存图片
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 验证文件
                file_size = os.path.getsize(filepath)
                if file_size == 0:
                    os.remove(filepath)
                    raise Exception("下载的文件大小为 0")
                
                self.stats["success"] += 1
                self.stats["bytes_downloaded"] += file_size
                
                return True, f"下载成功：{filepath} ({file_size} bytes)"
                
            except (Timeout, ConnectionError) as e:
                if attempt < self.MAX_RETRIES:
                    print(f"  下载超时/连接错误，{self.RETRY_DELAY}秒后重试 ({attempt}/{self.MAX_RETRIES}): {url}")
                    time.sleep(self.RETRY_DELAY)
                else:
                    self.stats["failed"] += 1
                    return False, f"下载失败（重试{self.MAX_RETRIES}次后仍失败）: {e}"
                    
            except RequestException as e:
                self.stats["failed"] += 1
                return False, f"下载失败：{e}"
        
        self.stats["failed"] += 1
        return False, "下载失败（未知错误）"
    
    def download_images(self, cards: List[Dict], pack_id: str = None, 
                       delay: float = 0.1) -> Dict:
        """
        批量下载图片
        
        Args:
            cards: 卡牌数据列表（每个元素应包含 image_url 字段）
            pack_id: 卡包 ID（可选）
            delay: 下载间隔（秒），避免请求过快
            
        Returns:
            下载统计信息
        """
        print(f"\n[DOWNLOAD] 开始批量下载图片，共 {len(cards)} 张卡牌")
        
        # 重置统计
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "bytes_downloaded": 0
        }
        
        results = []
        
        for i, card in enumerate(cards):
            image_url = card.get('image_url') or card.get('imageUrl')
            
            if not image_url:
                print(f"  [{i+1}/{len(cards)}] 跳过：无图片 URL - {card.get('card_no', 'Unknown')}")
                self.stats["skipped"] += 1
                continue
            
            card_no = card.get('card_no', '')
            
            print(f"  [{i+1}/{len(cards)}] 下载：{card_no or 'Unknown'}", end="")
            
            success, message = self.download_image(
                url=image_url,
                card_no=card_no,
                pack_id=pack_id
            )
            
            if success:
                print(f" [OK]")
            else:
                print(f" [FAIL] {message}")
            
            results.append({
                "card_no": card_no,
                "image_url": image_url,
                "success": success,
                "message": message
            })
            
            # 礼貌性延迟
            if delay > 0 and i < len(cards) - 1:
                time.sleep(delay)
        
        # 打印统计
        self._print_stats()
        
        return {
            "stats": self.stats,
            "results": results
        }
    
    def download_from_urls(self, url_card_map: Dict[str, str], 
                          pack_id: str = None, delay: float = 0.1) -> Dict:
        """
        从 URL-卡牌编号映射批量下载
        
        Args:
            url_card_map: {image_url: card_no} 映射
            pack_id: 卡包 ID（可选）
            delay: 下载间隔（秒）
            
        Returns:
            下载统计信息
        """
        print(f"\n[DOWNLOAD] 开始批量下载图片，共 {len(url_card_map)} 张图片")
        
        # 重置统计
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "bytes_downloaded": 0
        }
        
        results = []
        
        for i, (url, card_no) in enumerate(url_card_map.items()):
            print(f"  [{i+1}/{len(url_card_map)}] 下载：{card_no or 'Unknown'}", end="")
            
            success, message = self.download_image(
                url=url,
                card_no=card_no,
                pack_id=pack_id
            )
            
            if success:
                print(f" [OK]")
            else:
                print(f" [FAIL] {message}")
            
            results.append({
                "card_no": card_no,
                "image_url": url,
                "success": success,
                "message": message
            })
            
            if delay > 0 and i < len(url_card_map) - 1:
                time.sleep(delay)
        
        self._print_stats()
        
        return {
            "stats": self.stats,
            "results": results
        }
    
    def _print_stats(self):
        """打印下载统计"""
        print(f"\n[STATS] 下载统计:")
        print(f"  总计：{self.stats['total']}")
        print(f"  成功：{self.stats['success']} [OK]")
        print(f"  失败：{self.stats['failed']} [FAIL]")
        print(f"  跳过：{self.stats['skipped']} [SKIP]")
        print(f"  总大小：{self._format_bytes(self.stats['bytes_downloaded'])}")
    
    def _format_bytes(self, size: int) -> str:
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def get_downloaded_images(self) -> List[str]:
        """
        获取已下载的图片文件列表
        
        Returns:
            图片文件路径列表
        """
        if not os.path.exists(self.raw_dir):
            return []
        
        files = []
        for f in os.listdir(self.raw_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                files.append(os.path.join(self.raw_dir, f))
        
        return sorted(files)
    
    def cleanup_failed_downloads(self):
        """清理下载失败的空文件"""
        if not os.path.exists(self.raw_dir):
            return
        
        cleaned = 0
        for f in os.listdir(self.raw_dir):
            filepath = os.path.join(self.raw_dir, f)
            if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
                try:
                    os.remove(filepath)
                    cleaned += 1
                except Exception as e:
                    print(f"清理失败 {filepath}: {e}")
        
        if cleaned > 0:
            print(f"[CLEAN] 清理了 {cleaned} 个空文件")
    
    def close(self):
        """关闭下载器，释放资源"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """测试函数"""
    import sys
    # 设置控制台编码为 UTF-8
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # 测试图片 URL
    test_urls = [
        ("https://digimoncard.com/images/cardlist/card/EX11-001.png?02", "EX11-001"),
        ("https://digimoncard.com/images/cardlist/card/EX11-002.png?02", "EX11-002"),
        ("https://digimoncard.com/images/cardlist/card/noimage.png", None),  # 无效
    ]
    
    print("[TEST] 图片下载器测试\n")
    
    with ImageDownloader() as downloader:
        for url, card_no in test_urls:
            print(f"测试：{card_no or 'Unknown'}")
            success, message = downloader.download_image(url, card_no)
            status = "OK" if success else "FAIL"
            print(f"  结果：[{status}] {message}\n")
        
        # 显示已下载的图片
        downloaded = downloader.get_downloaded_images()
        if downloaded:
            print(f"[FILES] 已下载的图片 ({len(downloaded)} 张):")
            for img in downloaded[:10]:  # 只显示前 10 张
                print(f"  - {os.path.basename(img)}")


if __name__ == "__main__":
    main()
