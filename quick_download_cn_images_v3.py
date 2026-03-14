"""
中文卡牌图片下载脚本 - v3
修复：在列表页点击"简中"按钮，然后再进入卡牌详情页
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


def click_language_switch_on_list_page(driver):
    """
    在列表页点击"简中"按钮
    
    返回列表：
    - True: 成功点击
    - False: 未找到按钮或点击失败
    """
    logger.info("在列表页查找语言切换按钮...")
    
    # 等待页面加载
    time.sleep(2)
    
    # 多种查找方式
    simplified_btn = None
    
    # 方法 1: 查找包含"简中"文本的按钮
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            btn_text = btn.text.strip()
            if "简中" in btn_text or "CN" in btn_text or "中文" in btn_text:
                simplified_btn = btn
                logger.info(f"找到简中按钮 (方法 1): {btn_text}")
                break
    except Exception as e:
        logger.debug(f"方法 1 查找失败：{e}")
    
    # 方法 2: XPath 查找
    if not simplified_btn:
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '简中') or contains(text(), 'CN')]")
            for elem in elements:
                if elem.tag_name in ['button', 'a', 'span', 'div']:
                    simplified_btn = elem
                    logger.info(f"找到简中按钮 (方法 2): {elem.tag_name}")
                    break
        except Exception as e:
            logger.debug(f"方法 2 查找失败：{e}")
    
    # 方法 3: 查找语言选择器
    if not simplified_btn:
        try:
            lang_selectors = driver.find_elements(By.CSS_SELECTOR, ".lang-selector, .language-switcher, [class*='lang'], [class*='language']")
            for selector in lang_selectors:
                if "简中" in selector.text or "CN" in selector.text:
                    simplified_btn = selector
                    logger.info(f"找到简中按钮 (方法 3): {selector.get_attribute('class')}")
                    break
        except Exception as e:
            logger.debug(f"方法 3 查找失败：{e}")
    
    if simplified_btn:
        try:
            logger.info("点击简中按钮...")
            simplified_btn.click()
            time.sleep(3)  # 等待语言切换生效
            logger.info("✅ 已切换到简体中文版本")
            return True
        except Exception as e:
            logger.warning(f"点击简中按钮失败：{e}")
            return False
    else:
        logger.warning("⚠️ 未找到简中按钮，可能已经是中文版本")
        return False


def download_cn_images():
    """
    下载中文卡牌图片
    
    关键修复：在列表页点击"简中"按钮，然后再进入卡牌详情页
    """
    logger.info("🎯 开始下载中文卡牌图片（列表页切换语言）")
    
    # 中文卡牌 URL 列表 - 使用已知存在的卡牌
    card_urls = [
        "https://app.digicamoe.cn/Cards/AD-01/AD1-025/SEC-P-1",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-024/SEC-P-1",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-016/SP",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-008/SP",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-007/SP",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-020/U",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-015/R",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-010/C",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-005/C",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-001/C",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-002/C",
        "https://app.digicamoe.cn/Cards/AD-01/AD1-003/C",
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
        
        # ⭐ 关键修复：先访问列表页，点击"简中"按钮
        list_page_url = "https://app.digicamoe.cn/Cards/AD-01"
        logger.info(f"访问列表页：{list_page_url}")
        driver.get(list_page_url)
        
        # 在列表页点击"简中"按钮
        language_switched = click_language_switch_on_list_page(driver)
        
        if language_switched:
            logger.info("✅ 语言已切换，现在访问卡牌详情页获取中文图片")
        else:
            logger.warning("⚠️ 语言切换可能未成功，继续执行")
        
        # 现在逐个访问卡牌详情页
        for i, card_url in enumerate(card_urls, 1):
            logger.info(f"处理卡牌 {i}/{len(card_urls)}: {card_url}")
            
            try:
                # 直接访问卡牌详情页（语言环境已设置）
                driver.get(card_url)
                
                # 等待图片元素加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.lazyLoad"))
                )
                time.sleep(2)
                
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
                stats["failed"] += 1
        
    finally:
        if driver:
            driver.quit()
            logger.info("Chrome WebDriver 已关闭")
    
    return stats


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 中文卡牌图片批量下载工具 - v3")
    print("修复：在列表页点击'简中'按钮后再进入详情页")
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
