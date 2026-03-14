"""
中文卡牌图片快速下载脚本 - 修复版
用于紧急完成中文图片下载任务
"""

import sys
import logging
from pathlib import Path
import time
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
    logger.info("Selenium 和 requests 模块已加载")
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.error(f"Selenium 未安装：{e}")


def download_cn_images():
    """
    下载中文卡牌图片
    
    使用正确的 CDN: dtcg-pics.moecard.cn
    """
    logger.info("🎯 开始下载中文卡牌图片")
    
    # 中文卡牌 URL 列表 - 使用已知存在的卡牌
    # 来自 AD-01 数码兽世代系列
    card_urls = [
        "https://app.digicamoe.cn/Cards/AD-01/AD1-025/SEC-P-1",  # 奥米加兽
        "https://app.digicamoe.cn/Cards/AD-01/AD1-024/SEC-P-1",  # 帝皇龙兽：战士形态
        "https://app.digicamoe.cn/Cards/AD-01/AD1-016/SP",       # 闪光暴龙兽
        "https://app.digicamoe.cn/Cards/AD-01/AD1-008/SP",       # 公爵兽
        "https://app.digicamoe.cn/Cards/AD-01/AD1-007/SP",       # 天狼星兽
        "https://app.digicamoe.cn/Cards/AD-01/AD1-020/U",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-015/R",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-010/C",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-005/C",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-001/C",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-002/C",        # 其他卡牌
        "https://app.digicamoe.cn/Cards/AD-01/AD1-003/C",        # 其他卡牌
    ]
    
    output_dir = project_root / "card_data" / "images" / "cn" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total": len(card_urls),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "files": []
    }
    
    driver = None
    try:
        # 设置 Chrome WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver 初始化完成")
        
        for i, card_url in enumerate(card_urls, 1):
            logger.info(f"处理卡牌 {i}/{len(card_urls)}: {card_url}")
            
            try:
                driver.get(card_url)
                
                # 等待页面加载，查找图片
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.lazyLoad"))
                )
                time.sleep(2)  # 额外等待图片加载
                
                # 查找所有 lazyLoad 图片
                img_elements = driver.find_elements(By.CSS_SELECTOR, "img.lazyLoad")
                
                image_url = None
                for img in img_elements:
                    src = img.get_attribute("src")
                    if src and "dtcg-pics.moecard.cn" in src:
                        image_url = src
                        logger.info(f"找到图片 URL: {src}")
                        break
                
                if not image_url:
                    logger.warning(f"未找到图片 URL: {card_url}")
                    stats["failed"] += 1
                    continue
                
                # 从 URL 生成文件名
                # 从卡牌 URL 中提取系列和编号
                match = re.search(r'/Cards/([^/]+)/([^/]+)', card_url)
                if match:
                    series = match.group(1)
                    card_no = match.group(2)
                    # 从图片 URL 中提取唯一标识
                    img_match = re.search(r'/card/([^/]+)\.jpg', image_url)
                    if img_match:
                        img_id = img_match.group(1).replace('.', '_')
                        filename = f"{series}_{card_no}_{img_id}.jpg"
                    else:
                        filename = f"{series}_{card_no}.jpg"
                else:
                    filename = f"card_{i:03d}.jpg"
                
                output_path = output_dir / filename
                
                # 检查是否已存在
                if output_path.exists():
                    logger.info(f"跳过已存在的文件：{filename}")
                    stats["skipped"] += 1
                    stats["files"].append(filename)
                    continue
                
                # 下载图片
                logger.info(f"下载图片：{image_url}")
                response = requests.get(image_url, timeout=30, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"下载成功：{filename}")
                stats["success"] += 1
                stats["files"].append(filename)
                
                # 避免请求过快
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"处理卡牌 {card_url} 时出错：{e}")
                stats["failed"] += 1
        
    finally:
        if driver:
            driver.quit()
            logger.info("Chrome WebDriver 已关闭")
    
    return stats


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 中文卡牌图片批量下载工具 - 修复版")
    print("=" * 60)
    print()
    
    if not SELENIUM_AVAILABLE:
        print("❌ 错误：Selenium 未安装")
        print("   请运行：pip install selenium webdriver-manager")
        return None
    
    result = download_cn_images()
    
    if result:
        print()
        print("=" * 60)
        print("📋 任务汇总报告")
        print("=" * 60)
        print(f"中文图片下载：{result['success']}/{result['total']} 张")
        print(f"失败：{result['failed']} 张")
        print(f"跳过：{result['skipped']} 张")
        
        if result['success'] >= 10:
            print("\n✅ 目标达成！图片数量已满足验证任务要求（≥10 张）")
        else:
            print(f"\n⏳ 还需下载 {max(0, 10 - result['success'])} 张才能达到目标")
        
        print(f"\n📁 输出目录：card_data/images/cn/raw/")
        if result['files']:
            print("\n下载的文件:")
            for filename in result['files']:
                print(f"   - {filename}")
        
        print("=" * 60)
    
    return result


if __name__ == "__main__":
    result = main()
    
    if result and result['success'] >= 10:
        sys.exit(0)
    else:
        sys.exit(1)
