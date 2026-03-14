"""
中文卡牌图片快速下载脚本
用于紧急完成中文图片下载任务
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

from image_downloader_skill.src.cn_downloader import ChineseImageDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_cn_images():
    """
    下载中文卡牌图片
    
    注意：中文图片需要从 app.digicamoe.cn 提取 URL
    这里提供一些示例 URL，实际使用时需要根据网站结构调整
    """
    logger.info("🎯 开始下载中文卡牌图片")
    
    # 示例卡牌 URL 列表（需要根据实际网站结构调整）
    # 这些是 BT25 系列的示例
    card_urls = [
        "https://app.digicamoe.cn/Cards/BT-25/BT25-001/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-002/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-003/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-004/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-005/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-006/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-007/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-008/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-009/C",
        "https://app.digicamoe.cn/Cards/BT-25/BT25-010/C",
    ]
    
    output_dir = project_root / "card_data" / "images" / "cn" / "raw"
    downloader = ChineseImageDownloader(str(output_dir))
    
    try:
        result = downloader.download_cards_from_urls(card_urls, output_prefix="")
        
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
        
    except Exception as e:
        logger.error(f"下载过程中发生错误：{e}")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 中文卡牌图片批量下载工具")
    print("=" * 60)
    print()
    print("⚠️  注意：中文图片下载需要 Selenium 和 Chrome")
    print("   如果未安装，请先运行：pip install selenium webdriver-manager")
    print()
    
    result = download_cn_images()
    
    if result:
        print()
        print("=" * 60)
        print("📋 任务汇总报告")
        print("=" * 60)
        print(f"中文图片下载：{result['success']}/{result['total']} 张")
        
        if result['success'] >= 10:
            print("\n✅ 目标达成！图片数量已满足验证任务要求（≥10 张）")
        else:
            print(f"\n⏳ 还需下载 {10 - result['success']} 张才能达到目标")
        
        print("=" * 60)
    
    return result


if __name__ == "__main__":
    result = main()
    
    if result and result['success'] >= 10:
        sys.exit(0)
    else:
        sys.exit(1)
