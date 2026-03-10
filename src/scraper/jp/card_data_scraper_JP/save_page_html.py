"""
Save page HTML for inspection
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--lang=ja")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(options=chrome_options)

url = "https://digimoncard.com/cards/?search=true&category=503035"
print(f"访问: {url}")
driver.get(url)
time.sleep(5)

# 保存HTML
html = driver.page_source
with open("output/page_source.html", "w", encoding="utf-8") as f:
    f.write(html)
print("HTML已保存到: output/page_source.html")

# 获取页面信息
info = driver.execute_script("""
    return {
        title: document.title,
        url: window.location.href,
        bodyText: document.body.innerText.substring(0, 500),
        allLinks: Array.from(document.querySelectorAll('a[href*="card_no"]')).length,
        allImages: document.querySelectorAll('img').length,
        allLis: document.querySelectorAll('li').length
    };
""")

print(f"\n页面标题: {info['title']}")
print(f"当前URL: {info['url']}")
print(f"包含card_no的链接数: {info['allLinks']}")
print(f"图片数: {info['allImages']}")
print(f"li元素数: {info['allLis']}")
print(f"\n页面文本前500字符:\n{info['bodyText']}")

driver.quit()
