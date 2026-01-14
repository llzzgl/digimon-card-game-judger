"""
检查页面中的详情元素
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

# 检查详情元素
result = driver.execute_script("""
    var result = {
        hasDetailDiv: false,
        detailIds: [],
        sampleDetailHtml: '',
        allDivIds: []
    };
    
    // 查找第一个卡牌的 data-src
    var firstLink = document.querySelector('a[data-src]');
    if (firstLink) {
        var dataSrc = firstLink.getAttribute('data-src');
        result.firstDataSrc = dataSrc;
        
        if (dataSrc) {
            var detailId = dataSrc.replace('#', '');
            var detailDiv = document.getElementById(detailId);
            
            if (detailDiv) {
                result.hasDetailDiv = true;
                result.sampleDetailHtml = detailDiv.outerHTML.substring(0, 1000);
            } else {
                result.hasDetailDiv = false;
                result.message = 'Detail div not found for ID: ' + detailId;
            }
        }
    }
    
    // 查找所有带ID的div
    var allDivs = document.querySelectorAll('div[id]');
    allDivs.forEach(function(div) {
        var id = div.id;
        if (id.match(/[A-Z]{2,3}\d{2}-\d{3}/)) {
            result.detailIds.push(id);
        }
        if (result.allDivIds.length < 10) {
            result.allDivIds.push(id);
        }
    });
    
    return result;
""")

print("\n=== 详情元素检查 ===")
print(f"第一个卡牌的 data-src: {result.get('firstDataSrc', 'N/A')}")
print(f"是否找到详情div: {result.get('hasDetailDiv', False)}")
print(f"找到的卡牌详情ID数量: {len(result.get('detailIds', []))}")
print(f"前10个div ID: {result.get('allDivIds', [])}")

if result.get('sampleDetailHtml'):
    print(f"\n示例详情HTML:\n{result['sampleDetailHtml']}")
else:
    print(f"\n消息: {result.get('message', 'No detail found')}")

driver.quit()
