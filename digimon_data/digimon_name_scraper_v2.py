"""
数码宝贝图鉴官网名称爬取器 v2
从 http://digimons.net 爬取官方中日文名称对照
修复编码问题和数据不全问题
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
import chardet


class DigimonNameScraperV2:
    def __init__(self):
        self.base_url = "http://digimons.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7',
        }
        self.name_mapping = {}  # 日文名 -> 中文名
        self.session = requests.Session()
        
    def _get_page(self, url: str) -> BeautifulSoup:
        """获取页面并正确处理编码"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            # 自动检测编码
            detected = chardet.detect(response.content)
            encoding = detected.get('encoding', 'utf-8')
            
            # 常见的日文网站编码
            if encoding and encoding.lower() in ['iso-8859-1', 'ascii']:
                # 尝试常见的日文编码
                for enc in ['utf-8', 'shift_jis', 'euc-jp', 'cp932']:
                    try:
                        response.content.decode(enc)
                        encoding = enc
                        break
                    except:
                        continue
            
            response.encoding = encoding
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None

    def fetch_digimon_list(self) -> list:
        """获取所有数码宝贝的链接列表"""
        print("正在获取数码宝贝列表...")
        digimon_links = set()
        
        # 尝试从索引页获取
        index_urls = [
            f"{self.base_url}/digimon/",
            f"{self.base_url}/digimon/index.html",
        ]
        
        for url in index_urls:
            soup = self._get_page(url)
            if soup:
                # 查找所有数码宝贝链接
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # 匹配 /digimon/xxx/ 或 /digimon/xxx/index.html 格式
                    match = re.search(r'/digimon/([a-z0-9_]+)(?:/|/index\.html)?$', href, re.I)
                    if match:
                        digimon_id = match.group(1).lower()
                        if digimon_id not in ['index', 'chn', 'jpn', 'eng']:
                            digimon_links.add(digimon_id)
        
        print(f"找到 {len(digimon_links)} 个数码宝贝链接")
        return list(digimon_links)

    def fetch_digimon_names(self, digimon_id: str) -> tuple:
        """获取单个数码宝贝的日文名和中文名"""
        jpn_name = None
        chn_name = None
        
        # 获取日文页面
        jpn_url = f"{self.base_url}/digimon/{digimon_id}/jpn.html"
        soup = self._get_page(jpn_url)
        if soup:
            # 尝试从标题获取日文名
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                # 通常格式: "数码兽名 - 数码兽图鉴"
                if '-' in title_text:
                    jpn_name = title_text.split('-')[0].strip()
                elif '|' in title_text:
                    jpn_name = title_text.split('|')[0].strip()
                else:
                    jpn_name = title_text.strip()
            
            # 也尝试从 h1 或特定元素获取
            if not jpn_name:
                h1 = soup.find('h1')
                if h1:
                    jpn_name = h1.get_text(strip=True)
        
        # 获取中文页面
        chn_url = f"{self.base_url}/digimon/{digimon_id}/chn.html"
        soup = self._get_page(chn_url)
        if soup:
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                if '-' in title_text:
                    chn_name = title_text.split('-')[0].strip()
                elif '|' in title_text:
                    chn_name = title_text.split('|')[0].strip()
                else:
                    chn_name = title_text.strip()
            
            if not chn_name:
                h1 = soup.find('h1')
                if h1:
                    chn_name = h1.get_text(strip=True)
        
        # 如果没有中文页面，尝试从主页面获取
        if not chn_name:
            main_url = f"{self.base_url}/digimon/{digimon_id}/"
            soup = self._get_page(main_url)
            if soup:
                # 查找中文名称（可能在特定元素中）
                for elem in soup.find_all(['span', 'div', 'td'], class_=re.compile(r'chn|chinese|cn', re.I)):
                    text = elem.get_text(strip=True)
                    if text and len(text) < 20:
                        chn_name = text
                        break
        
        return jpn_name, chn_name

    def scrape_all(self, delay: float = 0.3) -> dict:
        """爬取所有数码宝贝名称"""
        digimon_ids = self.fetch_digimon_list()
        
        if not digimon_ids:
            print("未找到数码宝贝列表，尝试使用备用方法...")
            # 备用：从已知的数码宝贝ID列表开始
            digimon_ids = self._get_known_digimon_ids()
        
        total = len(digimon_ids)
        for i, digimon_id in enumerate(digimon_ids, 1):
            jpn_name, chn_name = self.fetch_digimon_names(digimon_id)
            
            if jpn_name and chn_name:
                self.name_mapping[jpn_name] = chn_name
                print(f"[{i}/{total}] {jpn_name} -> {chn_name}")
            elif jpn_name:
                print(f"[{i}/{total}] {jpn_name} -> (无中文名)")
            else:
                print(f"[{i}/{total}] {digimon_id} -> (获取失败)")
            
            time.sleep(delay)
        
        print(f"\n完成！共获取 {len(self.name_mapping)} 个名称映射")
        return self.name_mapping

    def _get_known_digimon_ids(self) -> list:
        """返回已知的数码宝贝ID列表（备用）"""
        # 这是一个基础列表，可以手动扩展
        return [
            'agumon', 'gabumon', 'piyomon', 'tentomon', 'palmon', 'gomamon',
            'patamon', 'tailmon', 'greymon', 'garurumon', 'birdramon',
            'kabuterimon', 'togemon', 'ikkakumon', 'angemon', 'angewomon',
            'metalgreymon', 'weregarurumon', 'garudamon', 'atlurkabuterimon',
            'lilimon', 'zudomon', 'holyangemon', 'holydramon', 'wargreymon',
            'metalgarurumon', 'hououmon', 'helokabuterimon', 'rosemon',
            'vikemon', 'seraphimon', 'ofanimon', 'omegamon', 'imperialdramon',
            'dukemon', 'beelzebumon', 'sakuyamon', 'megidramon', 'guilmon',
            'terriermon', 'renamon', 'impmon', 'lopmon', 'culumon',
            'marineangemon', 'jesmon', 'alphamon', 'craniummon', 'duftmon',
            'dynasmon', 'lordknightmon', 'sleipmon', 'gankoomon', 'hackmon',
            'gammamon', 'jellymon', 'angoramon', 'diablomon', 'armagemon',
            'kuramon', 'tsumemon', 'keramon', 'chrysalimon', 'infermon',
            'dexmon', 'dorumon', 'dorugamon', 'doruguremon', 'dorugoramon',
            'ulforcevdramon', 'magnamon', 'veemon', 'exveemon', 'paildramon',
            'lucemon', 'lilithmon', 'barbamon', 'leviamon', 'daemon',
            'belphemon', 'ogudomon', 'piemon', 'metalseadramon', 'pinocchimon',
            'mugendramon', 'apocalymon', 'vamdemon', 'venomvamdemon',
            'belialvamdemon', 'etemon', 'metaletemon', 'kingetemon',
            'devimon', 'neodevimon', 'skullgreymon', 'blackwargreymon',
        ]

    def save_mapping(self, output_path: str):
        """保存名称映射到JSON文件"""
        # 按日文名排序
        sorted_mapping = dict(sorted(self.name_mapping.items()))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, ensure_ascii=False, indent=2)
        print(f"名称映射已保存到: {output_path}")

    def load_and_merge(self, existing_path: str):
        """加载现有映射并合并（保留现有数据）"""
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            
            # 合并，新数据优先（覆盖乱码）
            for jpn, chn in existing.items():
                # 检查是否有乱码
                if '�' not in chn and jpn not in self.name_mapping:
                    self.name_mapping[jpn] = chn
            
            print(f"合并后共 {len(self.name_mapping)} 个名称映射")
        except FileNotFoundError:
            print(f"文件不存在: {existing_path}")


def main():
    scraper = DigimonNameScraperV2()
    
    # 爬取名称
    scraper.scrape_all(delay=0.5)
    
    # 保存映射
    output_dir = Path(__file__).parent
    scraper.save_mapping(str(output_dir / "digimon_name_mapping_v2.json"))


if __name__ == "__main__":
    main()
