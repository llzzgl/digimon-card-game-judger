"""
检查单张卡牌的详情HTML
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--lang=ja")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(options=chrome_options)

url = "https://digimoncard.com/cards/?search=true&category=503035"
print(f"访问: {url}")
driver.get(url)
time.sleep(5)

# 查找一张数码宝贝卡（不是蛋卡或选项卡）的详情
result = driver.execute_script("""
    // 找一张Lv.3或以上的数码宝贝卡
    var detailDiv = document.getElementById('BT24-003'); // 应该是一张数码宝贝卡
    
    if (detailDiv) {
        return {
            found: true,
            html: detailDiv.outerHTML.substring(0, 5000)
        };
    }
    
    return {found: false};
""")

if result['found']:
    print("\n=== 卡牌详情HTML ===")
    print(result['html'])
else:
    print("未找到卡牌详情")

driver.quit()
