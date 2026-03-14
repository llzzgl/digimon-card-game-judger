"""
中文图片验证脚本
检查已下载的图片是否真的是简体中文版本
"""

import sys
import logging
from pathlib import Path
import re

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


def check_image_filenames():
    """检查图片文件名，分析可能的问题"""
    output_dir = project_root / "card_data" / "images" / "cn" / "raw"
    
    print("=" * 60)
    print("中文图片文件名分析")
    print("=" * 60)
    print()
    
    if not output_dir.exists():
        print(f"❌ 目录不存在：{output_dir}")
        return
    
    files = list(output_dir.glob("*.jpg"))
    print(f"找到 {len(files)} 张图片:\n")
    
    for f in sorted(files):
        print(f"  {f.name}")
    
    print()
    
    # 分析文件名模式
    print("文件名模式分析:")
    for f in sorted(files):
        name = f.name
        # 检查是否包含日文特征
        if "jpg~card" in name:
            print(f"  ⚠️  {name} - 包含 'jpg~card' 后缀 (可能是 CDN 缓存键)")
        else:
            print(f"  ✓  {name}")
    
    return files


def analyze_cdn_url():
    """分析 CDN URL 结构，判断是否区分语言版本"""
    print()
    print("=" * 60)
    print("CDN URL 结构分析")
    print("=" * 60)
    print()
    
    print("观察到的 CDN URL 模式:")
    print("  https://dtcg-pics.moecard.cn/img/card/{hash}_jpg~card.jpg")
    print()
    print("⚠️  关键问题:")
    print("  1. CDN URL 使用哈希值标识图片")
    print("  2. 同一张卡牌的日文和中文版本可能有不同的哈希值")
    print("  3. 但网页上的图片元素 src 可能不随语言切换而改变")
    print()
    print("可能的原因:")
    print("  - 语言切换只改变文字描述，不改变卡牌图片")
    print("  - 卡牌图片本身是日文的，中文只有规则书翻译")
    print("  - 需要检查卡牌详情页是否有'中文卡图'选项")
    print()


def suggest_solutions():
    """建议解决方案"""
    print("=" * 60)
    print("建议的解决方案")
    print("=" * 60)
    print()
    
    print("方案 1: 检查网页是否有独立的'中文卡图'选项")
    print("  - 有些游戏只有规则书翻译，卡牌图片保持日文原版")
    print("  - 需要确认 DTCG 官方是否提供中文卡图")
    print()
    
    print("方案 2: 检查图片元素的 data- 属性")
    print("  - 可能中文图片 URL 在 data-cn-src 等属性中")
    print("  - 需要检查页面的完整 HTML")
    print()
    
    print("方案 3: 检查网络请求")
    print("  - 语言切换可能触发新的 API 请求")
    print("  - 需要拦截网络请求找到中文图片 URL")
    print()
    
    print("方案 4: 接受日文卡图现实")
    print("  - 如果官方只提供日文卡图，这是正常的")
    print("  - 中文翻译只针对规则书和裁定 QA")
    print()


def main():
    """主函数"""
    check_image_filenames()
    analyze_cdn_url()
    suggest_solutions()
    
    print()
    print("=" * 60)
    print("建议下一步:")
    print("  1. 手动访问 https://app.digicamoe.cn/Cards/AD-01/AD1-025/SEC-P-1")
    print("  2. 点击'简中'按钮")
    print("  3. 检查卡牌图片是否真的变成中文")
    print("  4. 如果图片不变，说明官方只提供日文卡图")
    print("=" * 60)


if __name__ == "__main__":
    main()
