"""
数码宝贝图鉴官网名称爬取器
从 http://digimons.net/digimon/chn.html 爬取官方中文名称
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path


class DigimonNameScraper:
    def __init__(self):
        self.base_url = "http://digimons.net"
        self.list_url = f"{self.base_url}/digimon/chn.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.name_mapping = {}  # 日文名 -> 中文名
        
    def fetch_digimon_list(self) -> dict:
        """爬取数码宝贝名称列表"""
        print("正在爬取数码宝贝图鉴官网...")
        
        try:
            response = requests.get(self.list_url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有数码宝贝链接
            links = soup.find_all('a', href=re.compile(r'/digimon/'))
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 跳过导航链接
                if not text or 'chn.html' in href or 'jpn.html' in href:
                    continue
                
                # 尝试获取详情页以获取日文名
                if href and text:
                    self._process_digimon_link(href, text)
                    
            print(f"已爬取 {len(self.name_mapping)} 个数码宝贝名称")
            return self.name_mapping
            
        except Exception as e:
            print(f"爬取失败: {e}")
            return {}
    
    def _process_digimon_link(self, href: str, chinese_name: str):
        """处理单个数码宝贝链接，获取日文名"""
        try:
            # 从URL中提取数码宝贝ID
            # 例如: /digimon/agumon/ -> agumon
            match = re.search(r'/digimon/([^/]+)/', href)
            if match:
                digimon_id = match.group(1)
                
                # 尝试访问日文页面获取日文名
                jpn_url = f"{self.base_url}/digimon/{digimon_id}/jpn.html"
                
                response = requests.get(jpn_url, headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找日文名（通常在标题或特定元素中）
                title = soup.find('title')
                if title:
                    title_text = title.get_text()
                    # 提取日文名
                    jpn_name = title_text.split('-')[0].strip() if '-' in title_text else title_text.strip()
                    
                    if jpn_name and chinese_name:
                        self.name_mapping[jpn_name] = chinese_name
                        print(f"  {jpn_name} -> {chinese_name}")
                
                time.sleep(0.5)  # 避免请求过快
                
        except Exception as e:
            pass  # 静默处理单个失败
    
    def fetch_all_pages(self) -> dict:
        """爬取所有页面的数码宝贝名称"""
        print("正在爬取数码宝贝图鉴官网所有页面...")
        
        try:
            response = requests.get(self.list_url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找表格中的数码宝贝
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # 假设第一列是日文名，第二列是中文名
                        jpn_cell = cells[0].get_text(strip=True)
                        chn_cell = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        
                        if jpn_cell and chn_cell:
                            self.name_mapping[jpn_cell] = chn_cell
            
            # 也查找列表形式的数据
            items = soup.find_all(['li', 'div', 'span'])
            for item in items:
                text = item.get_text(strip=True)
                # 尝试解析 "日文名 / 中文名" 或 "日文名（中文名）" 格式
                if '/' in text:
                    parts = text.split('/')
                    if len(parts) == 2:
                        self.name_mapping[parts[0].strip()] = parts[1].strip()
                elif '（' in text and '）' in text:
                    match = re.match(r'(.+?)（(.+?)）', text)
                    if match:
                        self.name_mapping[match.group(1).strip()] = match.group(2).strip()
            
            print(f"已爬取 {len(self.name_mapping)} 个数码宝贝名称")
            return self.name_mapping
            
        except Exception as e:
            print(f"爬取失败: {e}")
            return {}
    
    def save_mapping(self, output_path: str):
        """保存名称映射到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.name_mapping, f, ensure_ascii=False, indent=2)
        print(f"名称映射已保存到: {output_path}")
    
    def load_mapping(self, input_path: str) -> dict:
        """从JSON文件加载名称映射"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.name_mapping = json.load(f)
            print(f"已加载 {len(self.name_mapping)} 个名称映射")
            return self.name_mapping
        except FileNotFoundError:
            print(f"文件不存在: {input_path}")
            return {}


def main():
    scraper = DigimonNameScraper()
    
    # 爬取名称
    scraper.fetch_all_pages()
    
    # 保存映射
    output_dir = Path(__file__).parent
    scraper.save_mapping(str(output_dir / "digimon_name_mapping.json"))


if __name__ == "__main__":
    main()
