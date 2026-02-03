"""
爬虫配置文件
可以在这里修改爬虫的各种参数
"""

# 目标URL
FAQ_URL = "https://app.digicamoe.cn/faq"

# 输出文件
OUTPUT_FILE = "official_qa.json"

# 浏览器设置
HEADLESS = True  # 是否使用无头模式（不显示浏览器窗口）
WINDOW_SIZE = "1920,1080"  # 浏览器窗口大小

# 等待时间设置（秒）
PAGE_LOAD_TIMEOUT = 20  # 页面加载超时时间
INITIAL_WAIT = 3  # 页面加载后的初始等待时间
ELEMENT_WAIT = 0.5  # 元素操作之间的等待时间

# 选择器配置
# 按优先级排列，爬虫会依次尝试这些选择器
SELECTORS = [
    ".ant-collapse-item",  # Ant Design Collapse 组件
    "[class*='faq']",      # 包含faq的class
    "[class*='question']", # 包含question的class
    "[class*='qa']",       # 包含qa的class
    ".ant-card",           # Ant Design Card 组件
    ".ant-list-item",      # Ant Design List 组件
]

# 数据源标识
DATA_SOURCE = "digicamoe_faq"

# 调试设置
DEBUG_MODE = False  # 是否启用调试模式
SAVE_DEBUG_HTML = True  # 失败时是否保存页面HTML
DEBUG_HTML_FILE = "faq_page_debug.html"  # 调试HTML文件名

# 重试设置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 5  # 重试延迟（秒）

# 日志设置
VERBOSE = True  # 是否显示详细日志


def get_chrome_options():
    """获取Chrome浏览器选项"""
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    
    if HEADLESS:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--window-size={WINDOW_SIZE}')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    return chrome_options


def print_config():
    """打印当前配置"""
    print("=" * 60)
    print("当前配置")
    print("=" * 60)
    print(f"目标URL: {FAQ_URL}")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"无头模式: {HEADLESS}")
    print(f"页面加载超时: {PAGE_LOAD_TIMEOUT}秒")
    print(f"调试模式: {DEBUG_MODE}")
    print(f"最大重试次数: {MAX_RETRIES}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
