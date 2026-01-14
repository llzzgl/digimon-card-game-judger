"""测试网站结构"""
import requests
from bs4 import BeautifulSoup

# 测试单个数码宝贝页面
url = "http://digimons.net/digimon/agumon/index.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers, timeout=30)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

print(f"Title: {soup.title.get_text() if soup.title else 'N/A'}")

# 查找日文名 - 通常在特定元素中
print("\n--- H1 标签 ---")
for h1 in soup.find_all('h1'):
    print(f"  {h1.get_text(strip=True)[:50]}")

print("\n--- H2 标签 ---")
for h2 in soup.find_all('h2'):
    print(f"  {h2.get_text(strip=True)[:50]}")

print("\n--- 查找包含日文名的元素 ---")
# 查找 class 包含 name 或 title 的元素
for elem in soup.find_all(['div', 'span', 'p', 'td', 'th'], class_=True):
    classes = ' '.join(elem.get('class', []))
    if 'name' in classes.lower() or 'title' in classes.lower() or 'jpn' in classes.lower():
        text = elem.get_text(strip=True)[:50]
        print(f"  {classes}: {text}")
