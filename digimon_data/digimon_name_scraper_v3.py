"""
数码宝贝图鉴官网名称爬取器 v3
从 http://digimons.net 爬取官方中日文名称对照
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path


class DigimonNameScraperV3:
    def __init__(self):
        self.base_url = "http://digimons.net/digimon"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.name_mapping = {}  # 日文名 -> 中文名
        self.session = requests.Session()
        
    def _get_page(self, url: str) -> BeautifulSoup:
        """获取页面"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None

    def get_digimon_list(self) -> list:
        """从中文检索页获取所有数码宝贝列表"""
        print("正在获取数码宝贝列表...")
        
        soup = self._get_page(f"{self.base_url}/chn.html")
        if not soup:
            return []
        
        digimon_list = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            chn_name = link.get_text(strip=True)
            
            # 匹配 xxx/index.html 格式的链接
            match = re.match(r'^([a-z0-9_]+)/index\.html$', href, re.I)
            if match and chn_name:
                digimon_id = match.group(1)
                digimon_list.append((digimon_id, chn_name))
        
        print(f"找到 {len(digimon_list)} 个数码宝贝")
        return digimon_list

    def get_japanese_name(self, digimon_id: str) -> str:
        """获取数码宝贝的日文名"""
        soup = self._get_page(f"{self.base_url}/{digimon_id}/index.html")
        if not soup:
            return None
        
        # 从 digimon_name class 元素中提取日文名
        name_elem = soup.find(class_='digimon_name')
        if name_elem:
            text = name_elem.get_text()
            # 查找 "日本語" 后面的日文名
            match = re.search(r'日本語\s*([ァ-ヶー・a-zA-Z0-9\s]+?)(?:English|简体中文|$)', text)
            if match:
                jpn_name = match.group(1).strip()
                # 清理名称
                jpn_name = re.sub(r'\s+', '', jpn_name)
                return jpn_name
        
        return None

    def scrape_all(self, delay: float = 0.2) -> dict:
        """爬取所有数码宝贝名称"""
        digimon_list = self.get_digimon_list()
        
        total = len(digimon_list)
        success = 0
        
        for i, (digimon_id, chn_name) in enumerate(digimon_list, 1):
            jpn_name = self.get_japanese_name(digimon_id)
            
            if jpn_name:
                self.name_mapping[jpn_name] = chn_name
                print(f"[{i}/{total}] {jpn_name} -> {chn_name}")
                success += 1
            else:
                print(f"[{i}/{total}] {digimon_id} ({chn_name}) -> 未找到日文名")
            
            time.sleep(delay)
        
        print(f"\n完成！成功获取 {success}/{total} 个名称映射")
        return self.name_mapping

    def save_mapping(self, output_path: str):
        """保存名称映射到JSON文件"""
        sorted_mapping = dict(sorted(self.name_mapping.items()))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, ensure_ascii=False, indent=2)
        print(f"名称映射已保存到: {output_path}")


def main():
    scraper = DigimonNameScraperV3()
    scraper.scrape_all(delay=0.2)
    
    output_dir = Path(__file__).parent
    scraper.save_mapping(str(output_dir / "digimon_name_mapping_v3.json"))


if __name__ == "__main__":
    main()
