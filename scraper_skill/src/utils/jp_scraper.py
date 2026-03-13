"""
日文卡牌爬虫
基于原有 card_data_scraper_JP/scraper.py 重构，保持原文件不动
"""
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict

# 导入原有爬虫（保持原文件不动）
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "card_data_scraper_JP"))
from models import Card, CardPack

logger = logging.getLogger(__name__)


class JapaneseCardScraper:
    """
    日文卡牌爬虫统一接口
    包装原有 scraper.py 的功能，提供配置化输出和错误处理
    """
    
    def __init__(self, config: dict = None):
        """
        初始化爬虫
        
        Args:
            config: 配置字典，包含 headless, output_dir 等
        """
        self.config = config or {}
        self.headless = self.config.get("headless", True)
        self.output_dir = Path(self.config.get("output_dir", "output"))
        self.driver = None
        self.wait = None
        
    def setup(self):
        """设置浏览器（复用原有逻辑）"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except ImportError:
            service = None
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={self.config.get('window_width', 1920)},{self.config.get('window_height', 1080)}")
        chrome_options.add_argument("--lang=ja")
        chrome_options.add_argument(f"user-agent={self.config.get('user_agent', 'Mozilla/5.0')}")
        
        try:
            if service:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.config.get("timeout", 30))
            logger.info("✓ Chrome 浏览器启动成功")
        except Exception as e:
            logger.error(f"❌ Chrome WebDriver 初始化失败：{e}")
            raise
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ 浏览器已关闭")
    
    def scrape_pack(self, category_id: str) -> tuple:
        """
        爬取单个卡包
        
        Args:
            category_id: 卡包 category ID
            
        Returns:
            (CardPack, List[Card])
        """
        from selenium.webdriver.common.by import By
        import re
        
        if not self.driver:
            self.setup()
        
        BASE_URL = "https://digimoncard.com"
        pack_url = f"{BASE_URL}/cards/?search=true&category={category_id}"
        
        try:
            logger.info(f"正在爬取卡包：{category_id}")
            self.driver.get(pack_url)
            time.sleep(3)
            
            # 获取卡包名称
            pack_name = ""
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, .page_title, title")
                pack_name = title_elem.text.strip()
            except:
                pass
            
            pack = CardPack(
                pack_id=category_id,
                pack_name=pack_name,
                pack_code=self._extract_pack_code(pack_name),
                release_date=None,
                pack_url=pack_url
            )
            
            cards = self._scrape_cards_from_page(pack)
            pack.card_count = len(cards)
            
            logger.info(f"✓ 卡包 {pack_name} 爬取完成，共 {len(cards)} 张卡牌")
            return pack, cards
            
        except Exception as e:
            logger.error(f"❌ 爬取卡包失败：{e}")
            raise
    
    def _extract_pack_code(self, pack_name: str) -> str:
        """从卡包名称提取卡包代码"""
        import re
        match = re.search(r'[A-Z]{2,3}-?\d{1,2}', pack_name)
        return match.group() if match else ""
    
    def _scrape_cards_from_page(self, pack: CardPack) -> List[Card]:
        """从页面爬取卡牌列表"""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        import re
        
        cards = []
        
        try:
            # 等待卡牌列表加载
            card_elements = self.wait.until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".card-item, .cardlist_item, .image_lists li")
            )
            
            logger.info(f"发现 {len(card_elements)} 张卡牌")
            
            for idx, card_elem in enumerate(card_elements):
                try:
                    card = self._parse_card_element(card_elem, pack)
                    if card:
                        cards.append(card)
                        logger.debug(f"  [{idx+1}/{len(card_elements)}] {card.card_no}: {card.card_name}")
                except Exception as e:
                    logger.warning(f"  解析卡牌失败：{e}")
            
        except TimeoutException:
            logger.warning("卡包页面加载超时")
        except Exception as e:
            logger.error(f"获取卡牌失败：{e}")
        
        return cards
    
    def _parse_card_element(self, elem, pack: CardPack) -> Optional[Card]:
        """解析单个卡牌元素"""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        import re
        
        try:
            card_link = elem.find_element(By.TAG_NAME, "a")
            card_url = card_link.get_attribute("href")
            
            try:
                img_elem = elem.find_element(By.TAG_NAME, "img")
                image_url = img_elem.get_attribute("src")
            except NoSuchElementException:
                image_url = None
            
            card_no = self._extract_card_no(elem, card_url)
            card_data = self._get_card_details(card_url)
            
            if card_data:
                return Card(
                    card_no=card_no or card_data.get("card_no", ""),
                    card_name=card_data.get("card_name", ""),
                    card_name_ruby=card_data.get("card_name_ruby"),
                    card_type=card_data.get("card_type", ""),
                    color=card_data.get("color", ""),
                    color2=card_data.get("color2"),
                    level=card_data.get("level"),
                    cost=card_data.get("cost"),
                    dp=card_data.get("dp"),
                    digivolve_cost1=card_data.get("digivolve_cost1"),
                    digivolve_cost2=card_data.get("digivolve_cost2"),
                    digivolve_color1=card_data.get("digivolve_color1"),
                    digivolve_color2=card_data.get("digivolve_color2"),
                    form=card_data.get("form"),
                    attribute=card_data.get("attribute"),
                    digimon_type=card_data.get("digimon_type"),
                    effect=card_data.get("effect"),
                    inherited_effect=card_data.get("inherited_effect"),
                    security_effect=card_data.get("security_effect"),
                    rarity=card_data.get("rarity", ""),
                    image_url=image_url or card_data.get("image_url"),
                    parallel_id=card_data.get("parallel_id"),
                    pack_id=pack.pack_id,
                    pack_name=pack.pack_name,
                    card_url=card_url
                )
        except Exception as e:
            logger.warning(f"    解析卡牌元素失败：{e}")
        
        return None
    
    def _extract_card_no(self, elem, card_url: str) -> str:
        """从元素或 URL 中提取卡牌编号"""
        import re
        
        if card_url:
            match = re.search(r'card_no=([A-Z0-9-]+)', card_url)
            if match:
                return match.group(1)
        
        try:
            return elem.get_attribute("data-card-no") or ""
        except:
            pass
        
        try:
            text = elem.text
            match = re.search(r'[A-Z]{2,3}-?\d{2,3}', text)
            if match:
                return match.group()
        except:
            pass
        
        return ""
    
    def _get_card_details(self, card_url: str) -> Dict:
        """获取卡牌详情页信息"""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        import re
        
        details = {}
        original_window = self.driver.current_window_handle
        
        try:
            self.driver.execute_script(f"window.open('{card_url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(1.5)
            
            details = self._parse_card_detail_page()
            
        except Exception as e:
            logger.error(f"    获取卡牌详情失败：{e}")
        finally:
            self.driver.close()
            self.driver.switch_to.window(original_window)
        
        return details
    
    def _parse_card_detail_page(self) -> Dict:
        """解析卡牌详情页"""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        import re
        
        details = {}
        
        try:
            # 卡牌编号
            try:
                card_no_elem = self.driver.find_element(By.CSS_SELECTOR, ".card_no, .cardno, [class*='number']")
                details["card_no"] = card_no_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 卡牌名称
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, ".card_name, .cardname, h1, h2")
                details["card_name"] = name_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 卡牌类型
            try:
                type_elem = self.driver.find_element(By.CSS_SELECTOR, ".card_type, [class*='type']")
                details["card_type"] = type_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 颜色
            try:
                color_elem = self.driver.find_element(By.CSS_SELECTOR, ".color, [class*='color']")
                details["color"] = color_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 等级
            try:
                level_elem = self.driver.find_element(By.CSS_SELECTOR, ".level, .lv, [class*='level']")
                level_text = level_elem.text.strip()
                level_match = re.search(r'\d+', level_text)
                if level_match:
                    details["level"] = int(level_match.group())
            except (NoSuchElementException, ValueError):
                pass
            
            # 费用
            try:
                cost_elem = self.driver.find_element(By.CSS_SELECTOR, ".cost, .play_cost, [class*='cost']")
                cost_text = cost_elem.text.strip()
                cost_match = re.search(r'\d+', cost_text)
                if cost_match:
                    details["cost"] = int(cost_match.group())
            except (NoSuchElementException, ValueError):
                pass
            
            # DP
            try:
                dp_elem = self.driver.find_element(By.CSS_SELECTOR, ".dp, [class*='dp']")
                dp_text = dp_elem.text.strip()
                dp_match = re.search(r'\d+', dp_text)
                if dp_match:
                    details["dp"] = int(dp_match.group())
            except (NoSuchElementException, ValueError):
                pass
            
            # 形态
            try:
                form_elem = self.driver.find_element(By.CSS_SELECTOR, ".form, [class*='form']")
                details["form"] = form_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 属性
            try:
                attr_elem = self.driver.find_element(By.CSS_SELECTOR, ".attribute, [class*='attribute']")
                details["attribute"] = attr_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 类型
            try:
                dtype_elem = self.driver.find_element(By.CSS_SELECTOR, ".digimon_type, .type, [class*='type']")
                details["digimon_type"] = dtype_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 效果
            try:
                effect_elem = self.driver.find_element(By.CSS_SELECTOR, ".effect, .card_effect, [class*='effect']")
                details["effect"] = effect_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 进化源效果
            try:
                inherited_elem = self.driver.find_element(By.CSS_SELECTOR, ".inherited_effect, [class*='inherited']")
                details["inherited_effect"] = inherited_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 稀有度
            try:
                rarity_elem = self.driver.find_element(By.CSS_SELECTOR, ".rarity, [class*='rarity']")
                details["rarity"] = rarity_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # 卡图
            try:
                img_elem = self.driver.find_element(By.CSS_SELECTOR, ".card_img img, .cardimage img, .detail_image img")
                details["image_url"] = img_elem.get_attribute("src")
            except NoSuchElementException:
                pass
                
        except Exception as e:
            logger.error(f"    解析详情页失败：{e}")
        
        return details
    
    def save_to_json(self, cards: List[Card], output_path: Path = None) -> Path:
        """
        保存卡牌数据到 JSON
        
        Args:
            cards: 卡牌列表
            output_path: 输出路径（可选）
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            output_path = self.output_dir / "cards_jp.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [asdict(c) for c in cards]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ 数据已保存到：{output_path}")
        return output_path
    
    def scrape_all(self, category_ids: List[str] = None) -> List[Card]:
        """
        爬取所有指定卡包
        
        Args:
            category_ids: 卡包 ID 列表，如果为 None 则爬取所有
            
        Returns:
            卡牌列表
        """
        all_cards = []
        
        if category_ids is None:
            # 获取所有卡包 ID（需要实现）
            category_ids = self._get_all_category_ids()
        
        for idx, cat_id in enumerate(category_ids, 1):
            try:
                logger.info(f"\n[{idx}/{len(category_ids)}] 爬取卡包：{cat_id}")
                pack, cards = self.scrape_pack(cat_id)
                all_cards.extend(cards)
                time.sleep(self.config.get("request_delay", 1))
            except Exception as e:
                logger.error(f"卡包 {cat_id} 爬取失败：{e}")
                continue
        
        return all_cards
    
    def _get_all_category_ids(self) -> List[str]:
        """获取所有卡包 category ID"""
        # 这里可以复用原有 scraper.py 的 get_all_packs 逻辑
        # 为简化，返回一个示例列表
        logger.warning("未实现自动获取所有卡包 ID，返回空列表")
        return []
