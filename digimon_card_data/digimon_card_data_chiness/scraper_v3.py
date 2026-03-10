"""
数码兽卡牌中文数据爬虫 V3
支持增量保存和单卡更新
"""

import json
import re
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# 默认数据文件路径
DEFAULT_DATA_FILE = "digimon_cards_cn.json"


class DigimonCardDatabase:
    """卡牌数据库管理类"""
    
    def __init__(self, data_file=DEFAULT_DATA_FILE):
        self.data_file = data_file
        self.cards = {}  # 以card_no为key存储
        self.load()
    
    def load(self):
        """加载现有数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换为字典格式，以card_no为key
                    if isinstance(data, list):
                        for card in data:
                            if card.get('card_no'):
                                self.cards[card['card_no']] = card
                    elif isinstance(data, dict):
                        self.cards = data
                print(f"已加载 {len(self.cards)} 张卡牌数据")
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.cards = {}
        else:
            print(f"数据文件不存在，将创建新文件: {self.data_file}")
            self.cards = {}
    
    def save(self):
        """保存数据到文件"""
        # 转换为列表格式保存
        data_list = list(self.cards.values())
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
    
    def add_card(self, card_info, save_immediately=True):
        """添加或更新单张卡牌"""
        card_no = card_info.get('card_no')
        if not card_no:
            print("  ⚠ 卡牌编号为空，跳过")
            return False
        
        self.cards[card_no] = card_info
        
        if save_immediately:
            self.save()
        
        return True
    
    def get_card(self, card_no):
        """获取单张卡牌"""
        return self.cards.get(card_no)
    
    def has_card(self, card_no):
        """检查卡牌是否存在"""
        return card_no in self.cards
    
    def get_all_cards(self):
        """获取所有卡牌"""
        return list(self.cards.values())
    
    def count(self):
        """获取卡牌数量"""
        return len(self.cards)


class DigimonCardScraperV3:
    def __init__(self, headless=False, max_pages=None, data_file=DEFAULT_DATA_FILE):
        self.base_url = "https://app.digicamoe.cn/search"
        self.headless = headless
        self.max_pages = max_pages
        self.db = DigimonCardDatabase(data_file)
        
    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            driver = webdriver.Chrome(options=chrome_options)
        
        return driver
    
    def click_search_button(self, driver):
        """点击搜索按钮"""
        print("查找并点击搜索按钮...")
        time.sleep(3)
        
        selectors = [
            (By.XPATH, "//button[contains(text(), '搜索')]"),
            (By.XPATH, "//button[contains(@class, 'ant-btn-primary')]"),
            (By.XPATH, "//button[@type='button' and contains(., '搜索')]"),
            (By.CSS_SELECTOR, "button.ant-btn-primary"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]
        
        for by, selector in selectors:
            try:
                buttons = driver.find_elements(by, selector)
                for btn in buttons:
                    btn_text = btn.text.strip()
                    if '搜索' in btn_text or btn_text == '':
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.5)
                        try:
                            btn.click()
                            print(f"  ✓ 成功点击按钮")
                            time.sleep(3)
                            return True
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"  ✓ 使用JS成功点击按钮")
                                time.sleep(3)
                                return True
                            except:
                                continue
            except:
                continue
        
        print("  ✗ 未能点击搜索按钮")
        return False
    
    def get_card_links(self, driver):
        """获取当前页面的所有卡牌链接"""
        card_links = []
        time.sleep(2)
        
        all_links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and '/Cards/' in href and href not in card_links:
                    card_links.append(href)
            except:
                continue
        
        card_links = list(set(card_links))
        print(f"找到 {len(card_links)} 个卡牌链接")
        return card_links
    
    def parse_card_info(self, full_text, page_title, url):
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
        if type_match:
            card_info['type'] = type_match.group(1).strip()
        
        # 编号
        no_match = re.search(r'编\s*号\s+([A-Z0-9\-]+)', full_text)
        if no_match:
            card_info['card_no'] = no_match.group(1)
        
        # 罕贵度
        rarity_match = re.search(r'罕贵度\s+(\S+)', full_text)
        if rarity_match:
            card_info['rarity'] = rarity_match.group(1)
        
        # 颜色
        color_match = re.search(r'颜\s*色\s+(.+?)(?:\n|LV)', full_text)
        if color_match:
            card_info['color'] = color_match.group(1).strip()
        
        # 等级
        lv_match = re.search(r'LV\s*(\d+)', full_text)
        if lv_match:
            card_info['level'] = lv_match.group(1)
        
        # 登场费用
        play_cost_match = re.search(r'登场费用\s+(\d+)', full_text)
        if play_cost_match:
            card_info['play_cost'] = play_cost_match.group(1)
        
        # DP
        dp_match = re.search(r'DP\s+(\S+)', full_text)
        if dp_match:
            card_info['dp'] = dp_match.group(1)
        
        # 形态
        form_match = re.search(r'形\s*态\s+(.+?)(?:\n|属)', full_text)
        if form_match:
            card_info['form'] = form_match.group(1).strip()
        
        # 属性
        attr_match = re.search(r'属\s*性\s+(.+?)(?:\n|类)', full_text)
        if attr_match:
            card_info['attribute'] = attr_match.group(1).strip()
        
        # 类型/种类
        species_match = re.search(r'类\s*型\s+(.+?)(?:\n进化条件|进化\n|能力\n|效果\n)', full_text)
        if species_match:
            card_info['species'] = species_match.group(1).strip()
        
        # 进化条件
        evo_cond_match = re.search(r'进化条件[：:]\s*(.+?)(?:\n进化\n|能力|效果)', full_text, re.DOTALL)
        if evo_cond_match:
            card_info['evolution_condition'] = evo_cond_match.group(1).strip().replace('\n', ' ')
        
        # 能力/效果
        effect_match = re.search(r'能力\n(.+?)(?:进化源能力|安防效果|收录信息)', full_text, re.DOTALL)
        if effect_match:
            card_info['effect'] = effect_match.group(1).strip()
        else:
            effect_match2 = re.search(r'效果\n(.+?)(?:进化源能力|安防效果|收录信息)', full_text, re.DOTALL)
            if effect_match2:
                card_info['effect'] = effect_match2.group(1).strip()
        
        # 进化源能力
        inherited_match = re.search(r'进化源能力\n(.+?)(?:收录信息|卡片裁定|Page)', full_text, re.DOTALL)
        if inherited_match:
            card_info['inherited_effect'] = inherited_match.group(1).strip()
        
        # 安防效果
        security_match = re.search(r'安防效果\n(.+?)(?:收录信息|卡片裁定|Page)', full_text, re.DOTALL)
        if security_match:
            card_info['security_effect'] = security_match.group(1).strip()
        
        # 默认值
        for key in ['type', 'rarity', 'color', 'level', 'dp', 'form', 'attribute', 'species', 
                    'play_cost', 'evolution_condition', 'effect', 'inherited_effect', 'security_effect']:
            if key not in card_info:
                card_info[key] = ""
        
        # 添加更新时间
        card_info['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return card_info
    
    def extract_card_detail(self, driver):
        """提取卡牌详情"""
        try:
            time.sleep(2)
            page_title = driver.title
            url = driver.current_url
            body = driver.find_element(By.TAG_NAME, 'body')
            full_text = body.text
            
            card_info = self.parse_card_info(full_text, page_title, url)
            return card_info
        except Exception as e:
            return {'error': str(e), 'url': driver.current_url}
    
    def has_next_page(self, driver):
        """检查下一页"""
        try:
            # 查找下一页按钮（非禁用状态）
            next_btn = driver.find_element(By.CSS_SELECTOR, "li.ant-pagination-next:not(.ant-pagination-disabled)")
            return next_btn
        except:
            return None
    
    def scrape_single_card(self, card_url):
        """爬取单张卡牌"""
        driver = self.setup_driver()
        
        try:
            print(f"正在爬取: {card_url}")
            driver.get(card_url)
            
            card_info = self.extract_card_detail(driver)
            
            if card_info.get('card_no'):
                self.db.add_card(card_info)
                print(f"✓ 已保存: {card_info.get('card_no')} - {card_info.get('name_cn')}")
                return card_info
            else:
                print("✗ 无法获取卡牌信息")
                return None
                
        except Exception as e:
            print(f"错误: {e}")
            return None
        finally:
            driver.quit()
    
    def scrape_all_cards(self):
        """爬取所有卡牌"""
        driver = self.setup_driver()
        new_cards = 0
        skipped_cards = 0
        
        try:
            print(f"正在访问: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)
            
            if not self.click_search_button(driver):
                print("\n无法点击搜索按钮，等待15秒手动操作...")
                time.sleep(15)
            
            page_num = 1
            
            while True:
                if self.max_pages and page_num > self.max_pages:
                    print(f"\n已达到最大页数: {self.max_pages}")
                    break
                
                print(f"\n{'='*50}")
                print(f"第 {page_num} 页 | 数据库: {self.db.count()} 张卡牌")
                print(f"{'='*50}")
                
                card_links = self.get_card_links(driver)
                
                if not card_links:
                    print("未找到卡牌，等待5秒后重试...")
                    time.sleep(5)
                    card_links = self.get_card_links(driver)
                    if not card_links:
                        print("仍未找到卡牌，退出")
                        break
                
                for idx, card_url in enumerate(card_links, 1):
                    try:
                        card_no_from_url = card_url.split('/')[-2]
                        
                        # 检查是否已存在，已存在则跳过
                        if self.db.has_card(card_no_from_url):
                            print(f"[{idx}/{len(card_links)}] {card_no_from_url} ⏭ 已存在，跳过")
                            skipped_cards += 1
                            continue
                        
                        print(f"[{idx}/{len(card_links)}] {card_no_from_url}", end=" ")
                        
                        driver.execute_script(f"window.open('{card_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[-1])
                        
                        card_info = self.extract_card_detail(driver)
                        
                        if card_info.get('card_no'):
                            self.db.add_card(card_info, save_immediately=True)
                            new_cards += 1
                            print(f"✓ 新增 {card_info.get('name_cn', '')}")
                        else:
                            print("✗ 解析失败")
                        
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"✗ 错误: {e}")
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                
                # 下一页
                next_btn = self.has_next_page(driver)
                if next_btn:
                    print("\n点击下一页...")
                    try:
                        next_btn.click()
                        time.sleep(3)
                        page_num += 1
                    except:
                        break
                else:
                    print("\n没有更多页面")
                    break
            
            print(f"\n{'='*50}")
            print(f"完成！新增 {new_cards} 张，跳过 {skipped_cards} 张已存在卡牌")
            print(f"数据库共 {self.db.count()} 张卡牌")
            print(f"数据已保存到: {self.db.data_file}")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()


def update_single_card(card_url, data_file=DEFAULT_DATA_FILE):
    """更新单张卡牌的便捷函数"""
    scraper = DigimonCardScraperV3(headless=True, data_file=data_file)
    return scraper.scrape_single_card(card_url)


def scrape_all_cards(headless=True, max_pages=None, data_file=DEFAULT_DATA_FILE):
    """
    爬取所有卡牌的便捷函数
    
    Args:
        headless: 是否使用无头模式（默认True）
        max_pages: 最大爬取页数（默认None，爬取全部）
        data_file: 数据文件路径
    
    Returns:
        DigimonCardDatabase: 卡牌数据库对象
    
    Example:
        # 爬取所有卡牌
        db = scrape_all_cards()
        
        # 只爬取前5页
        db = scrape_all_cards(max_pages=5)
        
        # 显示浏览器窗口
        db = scrape_all_cards(headless=False)
    """
    scraper = DigimonCardScraperV3(headless=headless, max_pages=max_pages, data_file=data_file)
    scraper.scrape_all_cards()
    return scraper.db


def get_database(data_file=DEFAULT_DATA_FILE):
    """
    获取卡牌数据库对象（不启动爬虫）
    
    Returns:
        DigimonCardDatabase: 卡牌数据库对象
    
    Example:
        db = get_database()
        card = db.get_card("EX11-025")
        all_cards = db.get_all_cards()
        print(f"共 {db.count()} 张卡牌")
    """
    return DigimonCardDatabase(data_file)


def main():
    print("数码兽卡牌中文数据爬虫 V3")
    print("=" * 50)
    
    # headless=True 无头模式
    # max_pages=None 爬取所有页面
    scraper = DigimonCardScraperV3(headless=True, max_pages=None)
    scraper.scrape_all_cards()


if __name__ == "__main__":
    main()
