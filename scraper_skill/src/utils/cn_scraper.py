"""
中文卡牌爬虫
基于原有 digimon_card_data_chiness/scraper_v3.py 重构，保持原文件不动
"""
import json
import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChineseCardScraper:
    """
    中文卡牌爬虫统一接口
    包装原有 scraper_v3.py 的功能，提供配置化输出和错误处理
    """
    
    def __init__(self, config: dict = None):
        """
        初始化爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.headless = self.config.get("headless", True)
        self.base_url = self.config.get("base_url", "https://app.digicamoe.cn/search")
        self.output_path = Path(self.config.get("output_path", "digimon_cards_cn.json"))
        self.driver = None
        self.cards = {}  # 以 card_no 为 key 存储
        
    def setup(self):
        """设置浏览器"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'--window-size={self.config.get("window_width", 1920)},{self.config.get("window_height", 1080)}')
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        logger.info("✓ Chrome 浏览器启动成功")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ 浏览器已关闭")
    
    def load_existing_data(self):
        """加载现有数据"""
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for card in data:
                            if card.get('card_no'):
                                self.cards[card['card_no']] = card
                    elif isinstance(data, dict):
                        self.cards = data
                logger.info(f"✓ 已加载 {len(self.cards)} 张卡牌数据")
            except Exception as e:
                logger.error(f"加载数据失败：{e}")
                self.cards = {}
        else:
            logger.info(f"数据文件不存在，将创建新文件：{self.output_path}")
    
    def save_data(self):
        """保存数据到文件"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        data_list = list(self.cards.values())
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 数据已保存到：{self.output_path}")
    
    def scrape_single_card(self, card_url: str) -> Optional[Dict]:
        """
        爬取单张卡牌
        
        Args:
            card_url: 卡牌详情页 URL
            
        Returns:
            卡牌信息字典
        """
        if not self.driver:
            self.setup()
        
        try:
            logger.info(f"正在爬取：{card_url}")
            self.driver.get(card_url)
            time.sleep(2)
            
            card_info = self._extract_card_detail()
            
            if card_info and card_info.get('card_no'):
                self.cards[card_info['card_no']] = card_info
                self.save_data()
                logger.info(f"✓ 已保存：{card_info.get('card_no')} - {card_info.get('name_cn')}")
                return card_info
            else:
                logger.warning("✗ 无法获取卡牌信息")
                return None
                
        except Exception as e:
            logger.error(f"错误：{e}")
            return None
    
    def scrape_all_cards(self, max_pages: int = None) -> int:
        """
        爬取所有卡牌
        
        Args:
            max_pages: 最大页数（用于测试）
            
        Returns:
            新增卡牌数量
        """
        if not self.driver:
            self.setup()
        
        self.load_existing_data()
        new_cards = 0
        
        try:
            logger.info(f"正在访问：{self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(5)
            
            if not self._click_search_button():
                logger.warning("无法点击搜索按钮，等待 15 秒...")
                time.sleep(15)
            
            page_num = 1
            
            while True:
                if max_pages and page_num > max_pages:
                    logger.info(f"\n已达到最大页数：{max_pages}")
                    break
                
                logger.info(f"\n{'='*50}")
                logger.info(f"第 {page_num} 页 | 数据库：{len(self.cards)} 张卡牌")
                logger.info(f"{'='*50}")
                
                card_links = self._get_card_links()
                
                if not card_links:
                    logger.warning("未找到卡牌，等待 5 秒后重试...")
                    time.sleep(5)
                    card_links = self._get_card_links()
                    if not card_links:
                        logger.error("仍未找到卡牌，退出")
                        break
                
                for idx, card_url in enumerate(card_links, 1):
                    try:
                        card_no_from_url = card_url.split('/')[-2]
                        
                        if card_no_from_url in self.cards:
                            logger.debug(f"[{idx}/{len(card_links)}] {card_no_from_url} ⏭ 已存在，跳过")
                            continue
                        
                        logger.info(f"[{idx}/{len(card_links)}] {card_no_from_url}", end=" ")
                        
                        self.driver.execute_script(f"window.open('{card_url}', '_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        card_info = self._extract_card_detail()
                        
                        if card_info and card_info.get('card_no'):
                            self.cards[card_info['card_no']] = card_info
                            new_cards += 1
                            logger.info(f"✓ 新增 {card_info.get('name_cn', '')}")
                        else:
                            logger.warning("✗ 解析失败")
                        
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"✗ 错误：{e}")
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                
                # 下一页
                if not self._go_to_next_page():
                    break
                
                page_num += 1
                time.sleep(3)
            
            self.save_data()
            logger.info(f"\n✓ 爬取完成！新增 {new_cards} 张卡牌")
            return new_cards
            
        except Exception as e:
            logger.error(f"爬取失败：{e}")
            return 0
        finally:
            self.close()
    
    def _click_search_button(self) -> bool:
        """点击搜索按钮"""
        from selenium.webdriver.common.by import By
        
        logger.info("查找并点击搜索按钮...")
        time.sleep(3)
        
        selectors = [
            (By.XPATH, "//button[contains(text(), '搜索')]"),
            (By.XPATH, "//button[contains(@class, 'ant-btn-primary')]"),
            (By.CSS_SELECTOR, "button.ant-btn-primary"),
        ]
        
        for by, selector in selectors:
            try:
                buttons = self.driver.find_elements(by, selector)
                for btn in buttons:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.info(f"  ✓ 成功点击按钮")
                        time.sleep(3)
                        return True
                    except:
                        continue
            except:
                continue
        
        logger.warning("  ✗ 未能点击搜索按钮")
        return False
    
    def _get_card_links(self) -> List[str]:
        """获取当前页面的所有卡牌链接"""
        from selenium.webdriver.common.by import By
        
        time.sleep(2)
        card_links = []
        
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and '/Cards/' in href and href not in card_links:
                    card_links.append(href)
            except:
                continue
        
        card_links = list(set(card_links))
        logger.info(f"找到 {len(card_links)} 个卡牌链接")
        return card_links
    
    def _extract_card_detail(self) -> Optional[Dict]:
        """提取卡牌详情"""
        from selenium.webdriver.common.by import By
        
        try:
            time.sleep(2)
            page_title = self.driver.title
            url = self.driver.current_url
            body = self.driver.find_element(By.TAG_NAME, 'body')
            full_text = body.text
            
            return self._parse_card_info(full_text, page_title, url)
        except Exception as e:
            logger.error(f"提取卡牌详情失败：{e}")
            return {'error': str(e)}
    
    def _parse_card_info(self, full_text: str, page_title: str, url: str) -> Dict:
        """解析卡牌信息"""
        card_info = {'url': url}
        
        # 从标题解析
        title_match = re.search(r'(.+?)\s*\(([A-Z0-9\-]+)\s*\|\s*(.+?)\)', page_title)
        if title_match:
            card_info['name_cn'] = title_match.group(1).strip()
            card_info['card_no'] = title_match.group(2).strip()
            card_info['name_jp'] = title_match.group(3).strip()
        else:
            card_info['name_cn'] = ""
            card_info['card_no'] = ""
            card_info['name_jp'] = ""
        
        # 卡片类型
        type_match = re.search(r'卡片类型\s+(.+?)(?:\n|编)', full_text)
        card_info['type'] = type_match.group(1).strip() if type_match else ""
        
        # 编号
        no_match = re.search(r'编\s*号\s+([A-Z0-9\-]+)', full_text)
        if no_match:
            card_info['card_no'] = no_match.group(1)
        
        # 罕贵度
        rarity_match = re.search(r'罕贵度\s+(\S+)', full_text)
        card_info['rarity'] = rarity_match.group(1) if rarity_match else ""
        
        # 颜色
        color_match = re.search(r'颜\s*色\s+(.+?)(?:\n|LV)', full_text)
        card_info['color'] = color_match.group(1).strip() if color_match else ""
        
        # 等级
        lv_match = re.search(r'LV\s*(\d+)', full_text)
        card_info['level'] = lv_match.group(1) if lv_match else ""
        
        # 登场费用
        play_cost_match = re.search(r'登场费用\s+(\d+)', full_text)
        card_info['play_cost'] = play_cost_match.group(1) if play_cost_match else ""
        
        # DP
        dp_match = re.search(r'DP\s+(\S+)', full_text)
        card_info['dp'] = dp_match.group(1) if dp_match else ""
        
        # 形态
        form_match = re.search(r'形\s*态\s+(.+?)(?:\n|属)', full_text)
        card_info['form'] = form_match.group(1).strip() if form_match else ""
        
        # 属性
        attr_match = re.search(r'属\s*性\s+(.+?)(?:\n|类)', full_text)
        card_info['attribute'] = attr_match.group(1).strip() if attr_match else ""
        
        # 类型/种类
        species_match = re.search(r'类\s*型\s+(.+?)(?:\n进化条件|进化\n|能力\n|效果\n)', full_text)
        card_info['species'] = species_match.group(1).strip() if species_match else ""
        
        # 能力/效果
        effect_match = re.search(r'能力\n(.+?)(?:进化源能力 | 安防效果 | 收录信息)', full_text, re.DOTALL)
        if effect_match:
            card_info['effect'] = effect_match.group(1).strip()
        else:
            effect_match2 = re.search(r'效果\n(.+?)(?:进化源能力 | 安防效果 | 收录信息)', full_text, re.DOTALL)
            card_info['effect'] = effect_match2.group(1).strip() if effect_match2 else ""
        
        # 进化源能力
        inherited_match = re.search(r'进化源能力\n(.+?)(?:收录信息 | 卡片裁定|Page)', full_text, re.DOTALL)
        card_info['inherited_effect'] = inherited_match.group(1).strip() if inherited_match else ""
        
        # 安防效果
        security_match = re.search(r'安防效果\n(.+?)(?:收录信息 | 卡片裁定|Page)', full_text, re.DOTALL)
        card_info['security_effect'] = security_match.group(1).strip() if security_match else ""
        
        # 添加更新时间
        card_info['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return card_info
    
    def _go_to_next_page(self) -> bool:
        """翻到下一页"""
        from selenium.webdriver.common.by import By
        
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "li.ant-pagination-next:not(.ant-pagination-disabled)")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", next_btn)
            logger.info("  ✓ 已点击下一页")
            time.sleep(3)
            return True
        except:
            return False
    
    def has_card(self, card_no: str) -> bool:
        """检查卡牌是否已存在"""
        return card_no in self.cards
    
    def get_card(self, card_no: str) -> Optional[Dict]:
        """获取单张卡牌"""
        return self.cards.get(card_no)
    
    def get_all_cards(self) -> List[Dict]:
        """获取所有卡牌"""
        return list(self.cards.values())
