"""调试脚本：保存页面HTML以分析结构"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    service = Service(ChromeDriverManager().install())
except:
    service = None

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ja")

if service:
    driver = webdriver.Chrome(service=service, options=chrome_options)
else:
    driver = webdriver.Chrome(options=chrome_options)

url = "https://digimoncard.com/cards/?search=true&category=503035"
print(f"访问: {url}")
driver.get(url)

# 等待页面加载
time.sleep(8)

# 保存HTML
html = driver.page_source
with open("output/debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("HTML已保存到 output/debug_page.html")

# 打印一些关键信息
print("\n页面标题:", driver.title)
print("\n查找卡牌元素...")

# 尝试各种选择器
selectors = [
    ".image_lists li",
    ".cardlist_item", 
    ".card-item",
    ".card_list li",
    ".card_img",
    "ul li a img",
    ".modal_link",
    "[class*='card']",
    "a[href*='card_no']"
]

for sel in selectors:
    try:
        elems = driver.find_elements("css selector", sel)
        if elems:
            print(f"  {sel}: 找到 {len(elems)} 个元素")
    except:
        pass

driver.quit()
print("\n完成")
