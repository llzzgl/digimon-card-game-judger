"""
DTCG 卡牌图片统一下载器
支持中文和日文两个来源
"""

import logging
import argparse
from pathlib import Path
from typing import Optional

from .jp_downloader import JapaneseImageDownloader
from .cn_downloader import ChineseImageDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DTCGImageDownloader:
    """DTCG 卡牌图片统一下载器"""
    
    def __init__(self, cn_output_dir: Optional[str] = None, jp_output_dir: Optional[str] = None):
        """
        初始化下载器
        
        Args:
            cn_output_dir: 中文图片输出目录（默认：card_data/images/cn/raw）
            jp_output_dir: 日文图片输出目录（默认：card_data/images/jp/raw）
        """
        project_root = Path(__file__).parent.parent.parent
        
        self.cn_output_dir = cn_output_dir or str(project_root / "card_data" / "images" / "cn" / "raw")
        self.jp_output_dir = jp_output_dir or str(project_root / "card_data" / "images" / "jp" / "raw")
        
        self.cn_downloader = None
        self.jp_downloader = JapaneseImageDownloader(self.jp_output_dir)
        
        logger.info(f"DTCG 图片下载器初始化完成")
        logger.info(f"中文输出目录：{self.cn_output_dir}")
        logger.info(f"日文输出目录：{self.jp_output_dir}")
    
    def init_cn_downloader(self):
        """初始化中文下载器（延迟初始化）"""
        if self.cn_downloader is None:
            self.cn_downloader = ChineseImageDownloader(self.cn_output_dir)
    
    def download_jp_cards(self, series: str = "EX11", count: int = 10, skip_existing: bool = True) -> dict:
        """
        下载日文卡牌图片
        
        Args:
            series: 系列代码（如"EX11"）
            count: 下载数量
            skip_existing: 是否跳过已存在的文件
            
        Returns:
            下载统计信息
        """
        logger.info(f"开始下载日文卡牌 - 系列：{series}, 数量：{count}")
        return self.jp_downloader.download_cards(series, count, skip_existing)
    
    def download_cn_cards(self, card_urls: list, output_prefix: str = "") -> dict:
        """
        下载中文卡牌图片
        
        Args:
            card_urls: 卡牌详情页 URL 列表
            output_prefix: 输出文件名前缀
            
        Returns:
            下载统计信息
        """
        self.init_cn_downloader()
        logger.info(f"开始下载中文卡牌 - 数量：{len(card_urls)}")
        return self.cn_downloader.download_cards_from_urls(card_urls, output_prefix)
    
    def download_both(self, jp_series: str = "EX11", jp_count: int = 10, 
                      cn_urls: Optional[list] = None) -> dict:
        """
        同时下载日文和中文卡牌图片
        
        Args:
            jp_series: 日文系列代码
            jp_count: 日文下载数量
            cn_urls: 中文卡牌 URL 列表
            
        Returns:
            包含日文和中文下载统计的字典
        """
        results = {
            "japanese": self.download_jp_cards(jp_series, jp_count),
            "chinese": None
        }
        
        if cn_urls:
            results["chinese"] = self.download_cn_cards(cn_urls)
        
        return results


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="DTCG 卡牌图片下载器")
    parser.add_argument("--lang", choices=["jp", "cn", "both"], default="jp", 
                        help="下载语言：jp=日文，cn=中文，both=两者")
    parser.add_argument("--series", default="EX11", help="日文卡牌系列代码（如 EX11）")
    parser.add_argument("--count", type=int, default=10, help="下载数量")
    parser.add_argument("--cn-urls", nargs="+", help="中文卡牌 URL 列表")
    parser.add_argument("--output-prefix", default="", help="中文输出文件名前缀")
    
    args = parser.parse_args()
    
    downloader = DTCGImageDownloader()
    
    if args.lang in ["jp", "both"]:
        logger.info(f"下载日文卡牌：{args.series} 系列，{args.count} 张")
        jp_result = downloader.download_jp_cards(args.series, args.count)
        logger.info(f"日文下载完成：成功 {jp_result['success']}, 失败 {jp_result['failed']}, 跳过 {jp_result['skipped']}")
    
    if args.lang in ["cn", "both"] and args.cn_urls:
        logger.info(f"下载中文卡牌：{len(args.cn_urls)} 张")
        cn_result = downloader.download_cn_cards(args.cn_urls, args.output_prefix)
        logger.info(f"中文下载完成：成功 {cn_result['success']}, 失败 {cn_result['failed']}, 跳过 {cn_result['skipped']}")
    elif args.lang in ["cn", "both"] and not args.cn_urls:
        logger.warning("中文下载需要指定 --cn-urls 参数")


if __name__ == "__main__":
    main()
