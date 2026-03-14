"""
爬取中文官网 AD-01 卡包元数据
增补模式：只爬取缺失的 AD-01 卡包
"""

import sys
import logging
from pathlib import Path
import time
import json
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
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.error(f"Selenium 未安装：{e}")


def scrape_ad01_cards():
    """
    爬取中文官网 AD-01 卡包数据
    """
    logger.info("🎯 开始爬取 AD-01 卡包元数据（中文官网）")
    
    # 中文官网 AD-01 卡包列表页
    ad01_url = "https://app.digicamoe.cn/package/AD-01"
    
    cards_data = []
    
    driver = None
    try:
        # 设置 Chrome WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=zh-CN")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver 初始化完成")
        
        # 访问 AD-01 列表页
        logger.info(f"访问：{ad01_url}")
        driver.get(ad01_url)
        time.sleep(5)  # 等待页面加载
        
        # 查找所有卡牌链接
        logger.info("查找卡牌链接...")
        # 卡牌链接格式：/Cards/AD1-001, /Cards/AD1-002, etc.
        card_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/Cards/AD1-']")
        logger.info(f"找到 {len(card_links)} 个卡牌链接")
        
        # 逐个访问卡牌详情页
        for i, link in enumerate(card_links[:30], 1):  # 限制 30 张测试
            href = link.get_attribute("href")
            if not href or href in [c.get('card_url') for c in cards_data]:
                continue
            
            logger.info(f"处理卡牌 {i}/{min(30, len(card_links))}: {href}")
            
            try:
                driver.get(href)
                time.sleep(3)  # 等待页面加载
                
                # 提取卡牌信息
                card_info = extract_card_info(driver, href)
                if card_info:
                    cards_data.append(card_info)
                    logger.info(f"  ✓ {card_info.get('card_no', 'N/A')} - {card_info.get('card_name', 'N/A')}")
                
            except Exception as e:
                logger.error(f"处理卡牌失败：{e}")
        
        logger.info(f"爬取完成，共 {len(cards_data)} 张卡牌")
        
    except Exception as e:
        logger.error(f"爬取过程中出错：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            logger.info("Chrome WebDriver 已关闭")
    
    return cards_data


def extract_card_info(driver, url: str) -> dict:
    """从详情页提取卡牌信息"""
    card_info = {
        'card_url': url,
        'card_no': '',
        'card_name': '',
        'pack_name': 'AD-01 数码兽世代',
        'rarity': '',
        'card_type': '',
        'color': '',
        'level': '',
        'cost': '',
        'dp': '',
        'attribute': '',
        'digimon_type': '',
        'effect': '',
        'image_url': '',
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    
    try:
        # 从 URL 提取卡牌编号
        match = re.search(r'/Cards/([^/]+)/([^/]+)', url)
        if match:
            card_info['card_no'] = f"{match.group(1)}-{match.group(2)}"
        
        # 尝试提取卡牌名称
        try:
            title_elem = driver.find_element(By.CSS_SELECTOR, "h1, .card-name, .card-title")
            card_info['card_name'] = title_elem.text.strip()
        except:
            card_info['card_name'] = card_info['card_no']
        
        # 尝试提取稀有度
        try:
            rarity_elem = driver.find_element(By.CSS_SELECTOR, ".rarity, [class*='rarity']")
            card_info['rarity'] = rarity_elem.text.strip()
        except:
            pass
        
        # 尝试提取图片 URL
        try:
            img_elem = driver.find_element(By.CSS_SELECTOR, "img.lazyLoad, img.card-image")
            card_info['image_url'] = img_elem.get_attribute("src")
        except:
            pass
        
        # 尝试提取卡牌类型、颜色等信息
        try:
            info_elems = driver.find_elements(By.CSS_SELECTOR, ".card-info li, [class*='info'] span")
            for elem in info_elems:
                text = elem.text.strip()
                if 'LV' in text or 'Lv' in text:
                    card_info['level'] = text
                elif '费用' in text or 'COST' in text.upper():
                    card_info['cost'] = text
                elif 'DP' in text:
                    card_info['dp'] = text
        except:
            pass
        
    except Exception as e:
        logger.warning(f"提取信息失败：{e}")
    
    return card_info


def save_cards_data(cards_data: list, output_path: Path):
    """保存卡牌数据"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取现有数据（如果有）
    existing_data = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            logger.info(f"读取到现有数据 {len(existing_data)} 条")
        except:
            pass
    
    # 合并数据（去重）
    existing_ids = {c.get('card_no') for c in existing_data}
    new_cards = [c for c in cards_data if c.get('card_no') not in existing_ids]
    
    merged_data = existing_data + new_cards
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"保存完成：{len(merged_data)} 条记录 (新增 {len(new_cards)} 条)")
    
    return len(new_cards)


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG AD-01 卡包元数据爬取（增补模式）")
    print("=" * 60)
    print()
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium 未安装")
        print("   请运行：pip install selenium webdriver-manager")
        return 0
    
    # 爬取数据
    cards_data = scrape_ad01_cards()
    
    if not cards_data:
        print("\n⚠️ 未爬取到任何数据")
        return 0
    
    # 保存数据
    output_path = project_root / "digimon_card_data" / "digimon_cards_AD-01_cards.json"
    new_count = save_cards_data(cards_data, output_path)
    
    print()
    print("=" * 60)
    print("爬取完成")
    print("=" * 60)
    print(f"爬取卡牌：{len(cards_data)} 张")
    print(f"新增记录：{new_count} 条")
    print(f"输出文件：{output_path}")
    
    return len(cards_data)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
