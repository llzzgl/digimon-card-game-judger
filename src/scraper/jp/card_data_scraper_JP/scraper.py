"""
数码宝贝卡牌爬虫脚本
使用 Selenium 爬取 digimoncard.com 的卡牌信息
"""
import json
import time
import re
import os
from typing import List, Dict, Optional
from dataclasses import asdict
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False

from models import Card, CardPack


class DigimonCardScraper:
    """数码宝贝卡牌爬虫"""
    
    BASE_URL = "https://digimoncard.com"
    CARDLIST_URL = f"{BASE_URL}/cards/"
    
    def __init__(self, headless: bool = True, output_dir: str = "output", chrome_driver_path: str = None):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            output_dir: 输出目录
            chrome_driver_path: ChromeDriver路径（可选，如果不指定则自动下载）
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 配置Chrome选项
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=ja")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 初始化WebDriver
        service = None
        if chrome_driver_path:
            service = Service(executable_path=chrome_driver_path)
        elif USE_WEBDRIVER_MANAGER:
            try:
                service = Service(ChromeDriverManager().install())
            except Exception as e:
                print(f"webdriver-manager 安装失败: {e}")
                print("尝试使用系统Chrome...")
        
        try:
            if service:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"\n❌ Chrome WebDriver 初始化失败: {e}")
            print("\n请尝试以下解决方案:")
            print("1. 确保已安装 Chrome 浏览器")
            print("2. 手动下载 ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/")
            print("3. 使用 --driver-path 参数指定 ChromeDriver 路径")
            print("4. 或者安装 webdriver-manager: pip install webdriver-manager")
            raise
            
        self.wait = WebDriverWait(self.driver, 15)
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

    def get_all_packs(self) -> List[CardPack]:
        """
        获取所有卡包列表
        
        Returns:
            卡包列表
        """
        packs = []
        
        try:
            # 访问卡牌列表页面
            self.driver.get(f"{self.CARDLIST_URL}?search=true")
            time.sleep(3)
            
            # 等待页面加载完成，查找卡包选择器
            # 通常是一个下拉菜单或者列表
            pack_selector = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='category'], .category-list, #category"))
            )
            
            # 获取所有卡包选项
            options = pack_selector.find_elements(By.TAG_NAME, "option")
            
            for option in options:
                category_value = option.get_attribute("value")
                if category_value and category_value.strip():
                    pack_name = option.text.strip()
                    pack_code = self._extract_pack_code(pack_name)
                    
                    pack = CardPack(
                        pack_id=category_value,
                        pack_name=pack_name,
                        pack_code=pack_code,
                        release_date=None,
                        pack_url=f"{self.CARDLIST_URL}?search=true&category={category_value}"
                    )
                    packs.append(pack)
                    print(f"发现卡包: {pack_name} (ID: {category_value})")
                    
        except TimeoutException:
            print("页面加载超时，尝试备用方法...")
            packs = self._get_packs_from_api()
        except Exception as e:
            print(f"获取卡包列表失败: {e}")
            
        return packs
    
    def _extract_pack_code(self, pack_name: str) -> str:
        """从卡包名称中提取卡包代码"""
        # 匹配如 BT-24, ST-18, EX-08 等格式
        match = re.search(r'[A-Z]{2,3}-?\d{1,2}', pack_name)
        return match.group() if match else ""
    
    def _get_packs_from_api(self) -> List[CardPack]:
        """备用方法：尝试从API获取卡包列表"""
        # 这里可以添加备用的API调用逻辑
        return []
    
    def get_cards_from_pack(self, pack: CardPack) -> List[Card]:
        """
        获取指定卡包中的所有卡牌
        
        Args:
            pack: 卡包信息
            
        Returns:
            卡牌列表
        """
        cards = []
        
        try:
            print(f"\n正在爬取卡包: {pack.pack_name}")
            self.driver.get(pack.pack_url)
            time.sleep(3)
            
            # 等待卡牌列表加载
            card_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card-item, .cardlist_item, .image_lists li"))
            )
            
            print(f"发现 {len(card_elements)} 张卡牌")
            
            for idx, card_elem in enumerate(card_elements):
                try:
                    card = self._parse_card_element(card_elem, pack)
                    if card:
                        cards.append(card)
                        print(f"  [{idx+1}/{len(card_elements)}] {card.card_no}: {card.card_name}")
                except Exception as e:
                    print(f"  解析卡牌失败: {e}")
                    
            # 检查是否有分页
            cards.extend(self._handle_pagination(pack))
            
        except TimeoutException:
            print(f"卡包页面加载超时: {pack.pack_name}")
        except Exception as e:
            print(f"获取卡牌失败: {e}")
            
        pack.card_count = len(cards)
        return cards

    def _parse_card_element(self, elem, pack: CardPack) -> Optional[Card]:
        """
        解析单个卡牌元素
        
        Args:
            elem: Selenium元素
            pack: 所属卡包
            
        Returns:
            Card对象或None
        """
        try:
            # 尝试获取卡牌链接并点击查看详情
            card_link = elem.find_element(By.TAG_NAME, "a")
            card_url = card_link.get_attribute("href")
            
            # 获取卡图URL
            try:
                img_elem = elem.find_element(By.TAG_NAME, "img")
                image_url = img_elem.get_attribute("src")
            except NoSuchElementException:
                image_url = None
            
            # 获取卡牌编号（通常在图片alt或data属性中）
            card_no = self._extract_card_no(elem, card_url)
            
            # 打开卡牌详情页获取完整信息
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
            print(f"    解析卡牌元素失败: {e}")
            
        return None
    
    def _extract_card_no(self, elem, card_url: str) -> str:
        """从元素或URL中提取卡牌编号"""
        # 尝试从URL提取
        if card_url:
            match = re.search(r'card_no=([A-Z0-9-]+)', card_url)
            if match:
                return match.group(1)
        
        # 尝试从data属性提取
        try:
            return elem.get_attribute("data-card-no") or ""
        except:
            pass
            
        # 尝试从文本提取
        try:
            text = elem.text
            match = re.search(r'[A-Z]{2,3}-?\d{2,3}', text)
            if match:
                return match.group()
        except:
            pass
            
        return ""
    
    def _get_card_details(self, card_url: str) -> Dict:
        """
        获取卡牌详情页信息
        
        Args:
            card_url: 卡牌详情页URL
            
        Returns:
            卡牌详情字典
        """
        details = {}
        
        # 在新标签页打开详情页
        original_window = self.driver.current_window_handle
        self.driver.execute_script(f"window.open('{card_url}', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
        try:
            time.sleep(1.5)
            
            # 解析详情页内容
            details = self._parse_card_detail_page()
            
        except Exception as e:
            print(f"    获取卡牌详情失败: {e}")
        finally:
            # 关闭详情页，切回原窗口
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
        return details

    def _parse_card_detail_page(self) -> Dict:
        """解析卡牌详情页"""
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
            print(f"    解析详情页失败: {e}")
            
        return details
    
    def _handle_pagination(self, pack: CardPack) -> List[Card]:
        """处理分页"""
        additional_cards = []
        
        try:
            # 查找下一页按钮
            while True:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, ".next, .pagination .next, a[rel='next']")
                    if next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(2)
                        
                        card_elements = self.driver.find_elements(By.CSS_SELECTOR, ".card-item, .cardlist_item, .image_lists li")
                        for elem in card_elements:
                            card = self._parse_card_element(elem, pack)
                            if card:
                                additional_cards.append(card)
                    else:
                        break
                except NoSuchElementException:
                    break
        except Exception as e:
            print(f"处理分页失败: {e}")
            
        return additional_cards

    def save_to_json(self, packs: List[CardPack], cards: List[Card], filename: str = None):
        """
        保存数据到JSON文件
        
        Args:
            packs: 卡包列表
            cards: 卡牌列表
            filename: 文件名（不含扩展名）
        """
        if filename is None:
            filename = f"digimon_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 保存卡包数据
        packs_file = os.path.join(self.output_dir, f"{filename}_packs.json")
        with open(packs_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in packs], f, ensure_ascii=False, indent=2)
        print(f"\n卡包数据已保存到: {packs_file}")
        
        # 保存卡牌数据
        cards_file = os.path.join(self.output_dir, f"{filename}_cards.json")
        with open(cards_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(c) for c in cards], f, ensure_ascii=False, indent=2)
        print(f"卡牌数据已保存到: {cards_file}")
        
        # 保存汇总数据
        summary = {
            "total_packs": len(packs),
            "total_cards": len(cards),
            "scraped_at": datetime.now().isoformat(),
            "packs": [{"pack_id": p.pack_id, "pack_name": p.pack_name, "card_count": p.card_count} for p in packs]
        }
        summary_file = os.path.join(self.output_dir, f"{filename}_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"汇总数据已保存到: {summary_file}")
    
    def scrape_single_pack(self, category_id: str) -> tuple:
        """
        爬取单个卡包
        
        Args:
            category_id: 卡包category ID
            
        Returns:
            (CardPack, List[Card])
        """
        pack = CardPack(
            pack_id=category_id,
            pack_name="",
            pack_code="",
            release_date=None,
            pack_url=f"{self.CARDLIST_URL}?search=true&category={category_id}"
        )
        
        # 访问页面获取卡包名称
        self.driver.get(pack.pack_url)
        time.sleep(3)
        
        try:
            title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, .page_title, title")
            pack.pack_name = title_elem.text.strip()
            pack.pack_code = self._extract_pack_code(pack.pack_name)
        except:
            pass
        
        cards = self.get_cards_from_pack(pack)
        return pack, cards
    
    def scrape_all(self, max_packs: int = None) -> tuple:
        """
        爬取所有卡包和卡牌
        
        Args:
            max_packs: 最大爬取卡包数量（用于测试）
            
        Returns:
            (List[CardPack], List[Card])
        """
        all_packs = []
        all_cards = []
        
        packs = self.get_all_packs()
        
        if max_packs:
            packs = packs[:max_packs]
        
        for pack in packs:
            cards = self.get_cards_from_pack(pack)
            all_packs.append(pack)
            all_cards.extend(cards)
            
            # 礼貌性延迟，避免请求过快
            time.sleep(2)
        
        return all_packs, all_cards


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数码宝贝卡牌爬虫")
    parser.add_argument("--category", type=str, help="指定卡包category ID")
    parser.add_argument("--max-packs", type=int, help="最大爬取卡包数量")
    parser.add_argument("--output", type=str, default="output", help="输出目录")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="显示浏览器")
    parser.add_argument("--driver-path", type=str, help="ChromeDriver路径")
    
    args = parser.parse_args()
    
    with DigimonCardScraper(headless=args.headless, output_dir=args.output, chrome_driver_path=args.driver_path) as scraper:
        if args.category:
            # 爬取指定卡包
            pack, cards = scraper.scrape_single_pack(args.category)
            scraper.save_to_json([pack], cards)
        else:
            # 爬取所有卡包
            packs, cards = scraper.scrape_all(max_packs=args.max_packs)
            scraper.save_to_json(packs, cards)
    
    print("\n爬取完成!")


if __name__ == "__main__":
    main()
