"""
DTCG 图片下载器使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from image_downloader_skill.src.downloader import DTCGImageDownloader


def example_download_jp():
    """示例：下载日文卡牌图片"""
    print("=" * 60)
    print("示例 1: 下载日文 EX11 系列前 10 张卡牌图片")
    print("=" * 60)
    
    downloader = DTCGImageDownloader()
    result = downloader.download_jp_cards(series="EX11", count=10)
    
    print(f"\n下载结果:")
    print(f"  总数：{result['total']}")
    print(f"  成功：{result['success']}")
    print(f"  失败：{result['failed']}")
    print(f"  跳过：{result['skipped']}")
    print(f"  文件：{result['files']}")
    
    return result


def example_download_cn():
    """示例：下载中文卡牌图片"""
    print("=" * 60)
    print("示例 2: 下载中文卡牌图片")
    print("=" * 60)
    
    # 示例 URL（需要替换为实际的卡牌详情页 URL）
    card_urls = [
        "https://app.digicamoe.cn/Cards/BT-25/BT25-044/SR",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-045/SR",
        # 添加更多 URL...
    ]
    
    downloader = DTCGImageDownloader()
    result = downloader.download_cn_cards(card_urls, output_prefix="")
    
    print(f"\n下载结果:")
    print(f"  总数：{result['total']}")
    print(f"  成功：{result['success']}")
    print(f"  失败：{result['failed']}")
    print(f"  跳过：{result['skipped']}")
    print(f"  文件：{result['files']}")
    
    return result


def example_download_both():
    """示例：同时下载日文和中文卡牌图片"""
    print("=" * 60)
    print("示例 3: 同时下载日文和中文卡牌图片")
    print("=" * 60)
    
    downloader = DTCGImageDownloader()
    
    # 下载日文卡牌
    jp_result = downloader.download_jp_cards(series="EX11", count=10)
    print(f"\n日文下载结果：成功 {jp_result['success']}/{jp_result['total']}")
    
    # 下载中文卡牌（需要提供 URL 列表）
    # cn_urls = [...]
    # cn_result = downloader.download_cn_cards(cn_urls)
    # print(f"中文下载结果：成功 {cn_result['success']}/{cn_result['total']}")
    
    return {"japanese": jp_result}


def quick_download_jp_10():
    """快速下载：日文 EX11 前 10 张（用于紧急任务）"""
    print("🚀 快速下载日文 EX11 系列前 10 张卡牌图片...")
    
    downloader = DTCGImageDownloader()
    result = downloader.download_jp_cards(series="EX11", count=10, skip_existing=True)
    
    print(f"\n✅ 下载完成!")
    print(f"   成功：{result['success']} 张")
    print(f"   失败：{result['failed']} 张")
    print(f"   跳过：{result['skipped']} 张（已存在）")
    
    return result


if __name__ == "__main__":
    # 运行快速下载示例
    quick_download_jp_10()
    
    # 如需运行其他示例，取消注释：
    # example_download_jp()
    # example_download_cn()
    # example_download_both()
