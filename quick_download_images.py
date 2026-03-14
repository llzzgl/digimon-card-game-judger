"""
DTCG 图片批量下载快速脚本
工程师可以直接运行此脚本完成下载任务
"""

import sys
import logging
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from image_downloader_skill.src.downloader import DTCGImageDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_jp_images(series: str = "EX11", count: int = 10):
    """
    下载日文卡牌图片
    
    Args:
        series: 系列代码
        count: 下载数量
    """
    logger.info(f"🎯 开始下载日文卡牌图片 - 系列：{series}, 数量：{count}")
    
    downloader = DTCGImageDownloader()
    result = downloader.download_jp_cards(series=series, count=count, skip_existing=True)
    
    logger.info("=" * 60)
    logger.info("📊 下载完成统计")
    logger.info("=" * 60)
    logger.info(f"✅ 成功：{result['success']} 张")
    logger.info(f"❌ 失败：{result['failed']} 张")
    logger.info(f"⏭️  跳过：{result['skipped']} 张（已存在）")
    logger.info("=" * 60)
    
    if result['success'] > 0:
        logger.info(f"📁 下载的文件:")
        for filename in result['files']:
            logger.info(f"   - {filename}")
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 卡牌图片批量下载工具")
    print("=" * 60)
    print()
    
    # 下载日文 EX11 系列前 10 张
    print("🚀 任务 1: 下载日文 EX11 系列前 10 张卡牌图片")
    print("-" * 60)
    jp_result = download_jp_images(series="EX11", count=10)
    print()
    
    # 汇总报告
    print("=" * 60)
    print("📋 任务汇总报告")
    print("=" * 60)
    print(f"日文图片下载：{jp_result['success']}/{jp_result['total']} 张")
    
    # 检查是否达到目标
    total_success = jp_result['success']
    if total_success >= 10:
        print("\n✅ 目标达成！图片数量已满足验证任务要求（≥10 张）")
    else:
        print(f"\n⏳ 还需下载 {10 - total_success} 张才能达到目标")
    
    print("=" * 60)
    
    return jp_result


if __name__ == "__main__":
    result = main()
    
    # 返回状态码
    if result['success'] >= 10:
        sys.exit(0)  # 成功
    else:
        sys.exit(1)  # 未完成
