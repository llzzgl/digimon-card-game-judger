"""
中文卡牌图片下载脚本 - v4
使用正确的中文卡包 URL 格式：EX-11CN
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
    
    使用正确的中文卡包 URL 格式：EX-11CN
    """
    logger.info("🎯 开始下载中文卡牌图片（使用 EX-11CN URL）")
    
    # 中文卡牌 URL 列表 - 使用 EX-11CN 中文卡包
    # 来自 EX-11 数码宝贝联展 中文版本
    card_urls = [
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-001/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-002/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-003/U",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-004/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-005/R",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-006/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-007/U",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-008/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-009/R",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-010/C",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-011/U",
        "https://app.digicamoe.cn/Cards/EX-11CN/EX11-012/R",
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
                
                # 等待页面加载
                time.sleep(3)
                
                # 等待图片元素加载
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img.lazyLoad"))
                    )
                except:
                    logger.warning(f"未找到 lazyLoad 图片，尝试查找其他图片元素")
                    time.sleep(2)
                
                # 查找所有图片
                img_elements = driver.find_elements(By.TAG_NAME, "img")
                
                image_url = None
                for img in img_elements:
                    src = img.get_attribute("src")
                    data_src = img.get_attribute("data-src")
                    
                    # 优先查找包含 card 的图片
                    if src and "dtcg-pics.moecard.cn" in src and "card" in src:
                        image_url = src
                        logger.info(f"找到图片 URL (src): {src}")
                        break
                    elif data_src and "dtcg-pics.moecard.cn" in data_src and "card" in data_src:
                        image_url = data_src
                        logger.info(f"找到图片 URL (data-src): {data_src}")
                        break
                
                # 如果还没找到，尝试查找所有包含 dtcg-pics 的图片
                if not image_url:
                    for img in img_elements:
                        src = img.get_attribute("src")
                        if src and "dtcg-pics.moecard.cn" in src:
                            image_url = src
                            logger.info(f"找到图片 URL (备用): {src}")
                            break
                
                if not image_url:
                    logger.warning(f"未找到图片 URL: {card_url}")
                    
                    # 保存页面 HTML 用于调试
                    debug_html = project_root / "card_data" / "images" / "cn" / f"debug_page_{i}.html"
                    with open(debug_html, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    logger.info(f"页面 HTML 已保存：{debug_html}")
                    
                    stats["failed"] += 1
                    continue
                
                # 从 URL 生成文件名
                match = re.search(r'/Cards/([^/]+)/([^/]+)', card_url)
                if match:
                    series = match.group(1)
                    card_no = match.group(2)
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
                import traceback
                traceback.print_exc()
                stats["failed"] += 1
        
    finally:
        if driver:
            driver.quit()
            logger.info("Chrome WebDriver 已关闭")
    
    return stats


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 中文卡牌图片批量下载工具 - v4")
    print("使用正确的中文卡包 URL 格式：EX-11CN")
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
