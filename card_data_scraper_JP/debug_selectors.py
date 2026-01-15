"""
Debug script to inspect page structure
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--lang=ja")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

url = "https://digimoncard.com/cards/?search=true&category=503035"
print(f"访问: {url}")
driver.get(url)
time.sleep(5)

# 获取页面HTML结构
html_structure = driver.execute_script("""
    var result = {
        title: document.title,
        bodyClasses: document.body.className,
        mainContainers: [],
        cardElements: []
    };
    
    // 查找主要容器
    var containers = document.querySelectorAll('[class*="card"], [class*="list"], [id*="card"], [id*="list"]');
    containers.forEach(function(el) {
        if (el.children.length > 0) {
            result.mainContainers.push({
                tag: el.tagName,
                className: el.className,
                id: el.id,
                childCount: el.children.length
            });
        }
    });
    
    // 查找所有可能的卡牌元素
    var possibleCards = document.querySelectorAll('li, .item, [class*="card"]');
    var cardCount = 0;
    possibleCards.forEach(function(el) {
        var img = el.querySelector('img');
        var link = el.querySelector('a');
        if (img || link) {
            cardCount++;
            if (cardCount <= 5) {  // 只记录前5个
                result.cardElements.push({
                    tag: el.tagName,
                    className: el.className,
                    id: el.id,
                    hasImg: !!img,
                    hasLink: !!link,
                    imgSrc: img ? img.src : '',
                    linkHref: link ? link.href : ''
                });
            }
        }
    });
    result.totalPossibleCards = cardCount;
    
    return result;
""")

print("\n=== 页面结构分析 ===")
print(f"标题: {html_structure['title']}")
print(f"\n主要容器 ({len(html_structure['mainContainers'])} 个):")
for container in html_structure['mainContainers'][:10]:
    print(f"  {container['tag']}.{container['className']} (id={container['id']}) - {container['childCount']} 个子元素")

print(f"\n可能的卡牌元素 (共 {html_structure['totalPossibleCards']} 个，显示前5个):")
for card in html_structure['cardElements']:
    print(f"  {card['tag']}.{card['className']}")
    if card['hasImg']:
        print(f"    图片: {card['imgSrc'][:80]}...")
    if card['hasLink']:
        print(f"    链接: {card['linkHref'][:80]}...")

input("\n按回车键关闭浏览器...")
driver.quit()
