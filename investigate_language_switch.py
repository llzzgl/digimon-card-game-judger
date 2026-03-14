"""
DTCG 卡牌网站语言切换调查脚本
调查"简中"按钮是否真的改变卡牌图片
"""

import sys
import logging
from pathlib import Path
import time
import json

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


def investigate_language_switch():
    """
    调查语言切换是否影响卡牌图片
    """
    print("=" * 70)
    print("DTCG 卡牌网站语言切换调查")
    print("=" * 70)
    print()
    
    # 测试卡牌 URL
    test_url = "https://app.digicamoe.cn/Cards/AD-01/AD1-025/SEC-P-1"
    
    driver = None
    try:
        # 设置 Chrome WebDriver (有头模式，方便观察)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 注释掉，可以看到浏览器
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"打开卡牌页面：{test_url}")
        driver.get(test_url)
        time.sleep(3)
        
        # 获取初始状态
        print("\n【初始状态】")
        initial_data = capture_page_state(driver)
        print_page_state(initial_data)
        
        # 查找并点击"简中"按钮
        print("\n【查找语言切换按钮】")
        lang_buttons = find_language_buttons(driver)
        
        if not lang_buttons:
            print("❌ 未找到语言切换按钮")
            print("\n可能情况:")
            print("  1. 网站已经是中文版本，无需切换")
            print("  2. 语言切换按钮使用非标准元素")
            print("  3. 语言设置在用户账户中，不在页面内")
            return
        
        print(f"找到 {len(lang_buttons)} 个语言相关按钮:")
        for i, btn in enumerate(lang_buttons, 1):
            print(f"  {i}. 文本='{btn['text']}', 标签={btn['tag']}, 类={btn['class']}")
        
        # 尝试点击"简中"按钮
        simplified_btn = None
        for btn in lang_buttons:
            if "简中" in btn['text'] or "CN" in btn['text'] or "中文" in btn['text']:
                simplified_btn = btn
                print(f"\n点击简中按钮：{btn}")
                btn['element'].click()
                time.sleep(3)  # 等待切换
                break
        
        if not simplified_btn:
            print("\n⚠️ 未找到明确的'简中'按钮，尝试其他方式...")
            # 尝试点击第一个语言按钮
            if lang_buttons:
                print(f"点击第一个语言按钮：{lang_buttons[0]['text']}")
                lang_buttons[0]['element'].click()
                time.sleep(3)
        
        # 获取切换后状态
        print("\n【切换后状态】")
        post_switch_data = capture_page_state(driver)
        print_page_state(post_switch_data)
        
        # 对比变化
        print("\n【对比分析】")
        compare_states(initial_data, post_switch_data)
        
        # 保存完整 HTML 用于分析
        html_path = project_root / "card_data" / "images" / "cn" / "page_after_switch.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n页面 HTML 已保存：{html_path}")
        
    except Exception as e:
        logger.error(f"调查过程中出错：{e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


def capture_page_state(driver):
    """捕获页面状态"""
    state = {
        'url': driver.current_url,
        'title': driver.title,
        'images': [],
        'texts': [],
        'language_indicators': []
    }
    
    # 捕获所有图片
    imgs = driver.find_elements(By.TAG_NAME, "img")
    for img in imgs:
        src = img.get_attribute("src")
        data_src = img.get_attribute("data-src")
        alt = img.get_attribute("alt")
        if src or data_src:
            state['images'].append({
                'src': src,
                'data-src': data_src,
                'alt': alt
            })
    
    # 捕获可能的语言指示器
    indicators = driver.find_elements(By.CSS_SELECTOR, "[class*='lang'], [class*='language'], .lang-switcher, .language-selector")
    for ind in indicators:
        state['language_indicators'].append({
            'tag': ind.tag_name,
            'class': ind.get_attribute("class"),
            'text': ind.text.strip()
        })
    
    # 捕获卡牌名称和描述（判断语言）
    card_elements = driver.find_elements(By.CSS_SELECTOR, ".card-name, .card-title, .card-text, [class*='card'] h1, [class*='card'] h2")
    for elem in card_elements[:10]:
        text = elem.text.strip()
        if text:
            state['texts'].append(text)
    
    return state


def print_page_state(state):
    """打印页面状态"""
    print(f"URL: {state['url']}")
    print(f"标题：{state['title']}")
    
    print(f"\n图片 ({len(state['images'])} 张):")
    for i, img in enumerate(state['images'][:5], 1):
        src = img['src'] or img['data-src'] or 'N/A'
        if len(src) > 60:
            src = src[:60] + '...'
        print(f"  {i}. {src}")
        if img['alt']:
            print(f"     alt='{img['alt']}'")
    
    print(f"\n文本内容 ({len(state['texts'])} 项):")
    for i, text in enumerate(state['texts'][:5], 1):
        print(f"  {i}. {text[:50]}...")
    
    print(f"\n语言指示器 ({len(state['language_indicators'])} 个):")
    for i, ind in enumerate(state['language_indicators'], 1):
        print(f"  {i}. <{ind['tag']}> class='{ind['class']}' text='{ind['text']}'")


def find_language_buttons(driver):
    """查找语言切换按钮"""
    buttons = []
    
    # 方法 1: 查找所有按钮
    btn_elements = driver.find_elements(By.TAG_NAME, "button")
    for btn in btn_elements:
        text = btn.text.strip()
        if any(kw in text for kw in ["简中", "日文", "CN", "JP", "中文", "日本語", "语言", "Language"]):
            buttons.append({
                'element': btn,
                'text': text,
                'tag': btn.tag_name,
                'class': btn.get_attribute("class")
            })
    
    # 方法 2: XPath 查找
    xpath_btns = driver.find_elements(By.XPATH, "//*[contains(text(), '简中') or contains(text(), '日文') or contains(text(), 'CN') or contains(text(), 'JP')]")
    for btn in xpath_btns:
        if btn not in [b['element'] for b in buttons]:
            buttons.append({
                'element': btn,
                'text': btn.text.strip(),
                'tag': btn.tag_name,
                'class': btn.get_attribute("class") if btn.tag_name != 'selenium' else 'N/A'
            })
    
    return buttons


def compare_states(initial, post_switch):
    """对比切换前后的状态"""
    print("\n图片 URL 变化:")
    initial_urls = set(img['src'] for img in initial['images'] if img['src'])
    post_urls = set(img['src'] for img in post_switch['images'] if img['src'])
    
    if initial_urls == post_urls:
        print("  ⚠️  图片 URL **没有变化** - 语言切换不改变卡牌图片")
    else:
        print("  ✓ 图片 URL 发生变化:")
        added = post_urls - initial_urls
        removed = initial_urls - post_urls
        for url in added:
            print(f"    + {url[:80]}...")
        for url in removed:
            print(f"    - {url[:80]}...")
    
    print("\n文本内容变化:")
    initial_texts = set(initial['texts'])
    post_texts = set(post_switch['texts'])
    
    if initial_texts == post_texts:
        print("  ⚠️  文本内容**没有变化** - 语言切换可能未生效")
    else:
        print("  ✓ 文本内容发生变化")


def main():
    """主函数"""
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium 未安装，无法执行调查")
        print("   请运行：pip install selenium webdriver-manager")
        return
    
    investigate_language_switch()
    
    print()
    print("=" * 70)
    print("调查完成")
    print("=" * 70)
    print()
    print("结论:")
    print("  如果图片 URL 没有变化，说明:")
    print("  1. DTCG 官方只提供日文卡牌图片")
    print("  2. 中文翻译仅针对规则书和裁定 QA")
    print("  3. 这是正常的，不需要修复")
    print()
    print("建议:")
    print("  接受日文卡图作为正常情况，继续图片验证任务")


if __name__ == "__main__":
    main()
