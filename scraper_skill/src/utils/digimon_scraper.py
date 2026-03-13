"""
数码兽图鉴爬虫
基于原有 digimon_data/digimon_name_scraper_v3.py 重构，保持原文件不动
"""
import json
import time
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DigimonNameScraper:
    """
    数码兽名称爬虫统一接口
    从 digimons.net 爬取数码兽中日文名称对照
    """
    
    def __init__(self, config: dict = None):
        """
        初始化爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.base_url = self.config.get("base_url", "http://digimons.net/digimon")
        self.output_path = Path(self.config.get("output_path", "digimon_name_mapping.json"))
        self.delay = self.config.get("delay", 0.2)
        self.headers = {
            'User-Agent': self.config.get(
                'user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
        }
        self.name_mapping = {}  # 日文名 -> 中文名
        self.session = None
        
    def _setup_session(self):
        """设置请求会话"""
        import requests
        self.session = requests.Session()
        logger.info("✓ 请求会话已创建")
    
    def _get_page(self, url: str):
        """获取页面"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            from bs4 import BeautifulSoup
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"获取页面失败 {url}: {e}")
            return None
    
    def get_digimon_list(self) -> List[tuple]:
        """
        从中文检索页获取所有数码宝贝列表
        
        Returns:
            [(digimon_id, chn_name), ...]
        """
        logger.info("正在获取数码宝贝列表...")
        
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
        
        logger.info(f"找到 {len(digimon_list)} 个数码宝贝")
        return digimon_list
    
    def get_japanese_name(self, digimon_id: str) -> Optional[str]:
        """
        获取数码宝贝的日文名
        
        Args:
            digimon_id: 数码宝贝 ID（目录名）
            
        Returns:
            日文名或 None
        """
        soup = self._get_page(f"{self.base_url}/{digimon_id}/index.html")
        if not soup:
            return None
        
        # 从 digimon_name class 元素中提取日文名
        name_elem = soup.find(class_='digimon_name')
        if name_elem:
            text = name_elem.get_text()
            # 查找 "日本語" 后面的日文名
            match = re.search(r'日本語\s*([ァ - ヶー・a-zA-Z0-9\s]+?)(?:English|简体中文|$)', text)
            if match:
                jpn_name = match.group(1).strip()
                # 清理名称
                jpn_name = re.sub(r'\s+', '', jpn_name)
                return jpn_name
        
        return None
    
    def scrape_all(self, delay: float = None) -> Dict[str, str]:
        """
        爬取所有数码宝贝名称
        
        Args:
            delay: 请求延迟（秒）
            
        Returns:
            名称映射字典 {日文名：中文名}
        """
        if delay is None:
            delay = self.delay
        
        if not self.session:
            self._setup_session()
        
        digimon_list = self.get_digimon_list()
        
        total = len(digimon_list)
        success = 0
        
        for i, (digimon_id, chn_name) in enumerate(digimon_list, 1):
            jpn_name = self.get_japanese_name(digimon_id)
            
            if jpn_name:
                self.name_mapping[jpn_name] = chn_name
                logger.info(f"[{i}/{total}] {jpn_name} -> {chn_name}")
                success += 1
            else:
                logger.warning(f"[{i}/{total}] {digimon_id} ({chn_name}) -> 未找到日文名")
            
            time.sleep(delay)
        
        logger.info(f"\n完成！成功获取 {success}/{total} 个名称映射")
        return self.name_mapping
    
    def save_mapping(self, output_path: Path = None):
        """
        保存名称映射到 JSON 文件
        
        Args:
            output_path: 输出路径（可选）
        """
        if output_path is None:
            output_path = self.output_path
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 按日文名排序
        sorted_mapping = dict(sorted(self.name_mapping.items()))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, ensure_ascii=False, indent=2)
        
        logger.info(f"名称映射已保存到：{output_path}")
    
    def load_mapping(self, input_path: Path = None) -> Dict[str, str]:
        """
        从 JSON 文件加载名称映射
        
        Args:
            input_path: 输入路径（可选）
            
        Returns:
            名称映射字典
        """
        if input_path is None:
            input_path = self.output_path
        
        if not input_path.exists():
            logger.warning(f"文件不存在：{input_path}")
            return {}
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.name_mapping = json.load(f)
            logger.info(f"✓ 已加载 {len(self.name_mapping)} 个名称映射")
            return self.name_mapping
        except Exception as e:
            logger.error(f"加载失败：{e}")
            return {}
    
    def get_chinese_name(self, japanese_name: str) -> Optional[str]:
        """
        根据日文名获取中文名
        
        Args:
            japanese_name: 日文名
            
        Returns:
            中文名或 None
        """
        return self.name_mapping.get(japanese_name)
    
    def get_japanese_name(self, chinese_name: str) -> Optional[str]:
        """
        根据中文名获取日文名（反向查找）
        
        Args:
            chinese_name: 中文名
            
        Returns:
            日文名或 None
        """
        for jpn, chn in self.name_mapping.items():
            if chn == chinese_name:
                return jpn
        return None
