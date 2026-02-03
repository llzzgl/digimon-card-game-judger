"""
数码兽卡牌官方QA爬虫
从 https://app.digicamoe.cn/faq 爬取官方问答数据
"""

import json
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

# 尝试导入配置文件
try:
    from config import (
        FAQ_URL, OUTPUT_FILE, HEADLESS as DEFAULT_HEADLESS,
        PAGE_LOAD_TIMEOUT, INITIAL_WAIT, ELEMENT_WAIT,
        SELECTORS, DATA_SOURCE, SAVE_DEBUG_HTML, DEBUG_HTML_FILE
    )
except ImportError:
    # 如果配置文件不存在，使用默认值
    FAQ_URL = "https://app.digicamoe.cn/faq"
    OUTPUT_FILE = "official_qa.json"
    DEFAULT_HEADLESS = True
    PAGE_LOAD_TIMEOUT = 20
    INITIAL_WAIT = 3
    ELEMENT_WAIT = 0.5
    SELECTORS = [
        ".ant-collapse-item",
        "[class*='faq']",
        "[class*='question']",
        "[class*='qa']",
        ".ant-card",
        ".ant-list-item",
    ]
    DATA_SOURCE = "digicamoe_faq"
    SAVE_DEBUG_HTML = True
    DEBUG_HTML_FILE = "faq_page_debug.html"

# 默认数据文件路径
DEFAULT_DATA_FILE = OUTPUT_FILE


class FAQDatabase:
    """FAQ数据库管理类"""
    
    def __init__(self, data_file=DEFAULT_DATA_FILE):
        self.data_file = data_file
        self.qa_list = []
        self.load()
    
    def load(self):
        """加载现有数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.qa_list = json.load(f)
                print(f"已加载 {len(self.qa_list)} 条QA数据")
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.qa_list = []
        else:
            print(f"数据文件不存在，将创建新文件: {self.data_file}")
            self.qa_list = []
    
    def save(self):
        """保存数据到文件"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.qa_list, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(self.qa_list)} 条QA数据到 {self.data_file}")
    
    def add_qa(self, qa_info):
        """添加单条QA"""
        self.qa_list.append(qa_info)
    
    def clear(self):
        """清空数据"""
        self.qa_list = []
    
    def count(self):
        """获取QA数量"""
        return len(self.qa_list)


class DigimonFAQScraper:
    """数码兽卡牌FAQ爬虫"""
    
    def __init__(self, headless=None, data_file=None):
        self.base_url = FAQ_URL
        self.headless = headless if headless is not None else DEFAULT_HEADLESS
        self.data_file = data_file or DEFAULT_DATA_FILE
        self.db = FAQDatabase(self.data_file)
        
    def setup_driver(self):
        """设置浏览器驱动"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 尝试多种方式启动Chrome
        driver = None
        errors = []
        
        # 方法1: 使用webdriver-manager自动下载
        try:
            print("尝试使用webdriver-manager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✓ 成功使用webdriver-manager")
            return driver
        except Exception as e:
            errors.append(f"webdriver-manager失败: {str(e)[:100]}")
        
        # 方法2: 使用系统已安装的ChromeDriver
        try:
            print("尝试使用系统ChromeDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            print("✓ 成功使用系统ChromeDriver")
            return driver
        except Exception as e:
            errors.append(f"系统ChromeDriver失败: {str(e)[:100]}")
        
        # 方法3: 指定常见的ChromeDriver路径
        common_paths = [
            r"C:\chromedriver.exe",
            r"C:\Program Files\chromedriver.exe",
            r"C:\Windows\chromedriver.exe",
            "./chromedriver.exe",
            "chromedriver.exe"
        ]
        
        for path in common_paths:
            try:
                if os.path.exists(path):
                    print(f"尝试使用路径: {path}")
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print(f"✓ 成功使用: {path}")
                    return driver
            except Exception as e:
                errors.append(f"路径 {path} 失败: {str(e)[:50]}")
        
        # 所有方法都失败
        print("\n" + "="*60)
        print("❌ 无法启动Chrome浏览器")
        print("="*60)
        print("\n错误信息:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")
        
        print("\n解决方案:")
        print("1. 确保Chrome浏览器已安装")
        print("2. 手动下载ChromeDriver:")
        print("   - 访问: https://chromedriver.chromium.org/downloads")
        print("   - 或访问: https://googlechromelabs.github.io/chrome-for-testing/")
        print("   - 下载与Chrome版本匹配的ChromeDriver")
        print("   - 将chromedriver.exe放到以下任一位置:")
        print("     • 当前目录")
        print("     • C:\\chromedriver.exe")
        print("     • 系统PATH路径中")
        print("\n3. 检查网络连接（如果使用自动下载）")
        print("4. 使用代理或VPN（如果网络受限）")
        
        raise Exception("无法启动Chrome浏览器，请查看上述解决方案")
    
    def wait_for_page_load(self, driver, timeout=None):
        """等待页面加载完成"""
        if timeout is None:
            timeout = PAGE_LOAD_TIMEOUT
        try:
            # 等待页面主要内容加载
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(INITIAL_WAIT)  # 额外等待动态内容
            return True
        except Exception as e:
            print(f"页面加载超时: {e}")
            return False
    
    def extract_qa_items(self, driver):
        """提取QA条目"""
        qa_items = []
        
        try:
            # 尝试多种选择器来定位QA内容
            selectors = SELECTORS
            
            elements = []
            for selector in selectors:
                try:
                    found = driver.find_elements(By.CSS_SELECTOR, selector)
                    if found:
                        print(f"使用选择器 '{selector}' 找到 {len(found)} 个元素")
                        elements = found
                        break
                except:
                    continue
            
            if not elements:
                print("未找到QA元素，尝试获取页面文本...")
                # 如果找不到特定元素，尝试解析整个页面文本
                body = driver.find_element(By.TAG_NAME, 'body')
                page_text = body.text
                print(f"页面文本长度: {len(page_text)}")
                
                # 保存页面HTML用于调试
                if SAVE_DEBUG_HTML:
                    with open(DEBUG_HTML_FILE, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"已保存页面HTML到 {DEBUG_HTML_FILE} 用于调试")
                
                return qa_items
            
            # 解析找到的元素
            for idx, element in enumerate(elements, 1):
                try:
                    # 尝试提取问题和答案
                    question = ""
                    answer = ""
                    
                    # 方法1: Ant Design Collapse 结构
                    try:
                        header = element.find_element(By.CSS_SELECTOR, ".ant-collapse-header")
                        question = header.text.strip()
                        
                        # 点击展开（如果需要）
                        if "ant-collapse-item-active" not in element.get_attribute("class"):
                            header.click()
                            time.sleep(ELEMENT_WAIT)
                        
                        content = element.find_element(By.CSS_SELECTOR, ".ant-collapse-content")
                        answer = content.text.strip()
                    except:
                        pass
                    
                    # 方法2: 通用问答结构
                    if not question:
                        try:
                            # 查找包含"问"、"Q"、"question"的元素
                            q_elements = element.find_elements(By.XPATH, ".//*[contains(text(), '问') or contains(text(), 'Q:') or contains(text(), 'Q：')]")
                            if q_elements:
                                question = q_elements[0].text.strip()
                            
                            # 查找包含"答"、"A"、"answer"的元素
                            a_elements = element.find_elements(By.XPATH, ".//*[contains(text(), '答') or contains(text(), 'A:') or contains(text(), 'A：')]")
                            if a_elements:
                                answer = a_elements[0].text.strip()
                        except:
                            pass
                    
                    # 方法3: 直接使用元素文本
                    if not question:
                        element_text = element.text.strip()
                        if element_text:
                            # 尝试分割问答
                            lines = element_text.split('\n')
                            if len(lines) >= 2:
                                question = lines[0]
                                answer = '\n'.join(lines[1:])
                            else:
                                question = element_text
                    
                    if question:
                        qa_info = {
                            'question': question,
                            'answer': answer,
                            'source': DATA_SOURCE,
                            'url': self.base_url,
                            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'index': idx
                        }
                        qa_items.append(qa_info)
                        print(f"  [{idx}] Q: {question[:50]}...")
                
                except Exception as e:
                    print(f"  解析元素 {idx} 失败: {e}")
                    continue
        
        except Exception as e:
            print(f"提取QA失败: {e}")
            import traceback
            traceback.print_exc()
        
        return qa_items
    
    def scrape_faq(self):
        """爬取FAQ页面"""
        driver = self.setup_driver()
        
        try:
            print(f"正在访问: {self.base_url}")
            driver.get(self.base_url)
            
            if not self.wait_for_page_load(driver):
                print("页面加载失败")
                return
            
            print("\n开始提取QA内容...")
            qa_items = self.extract_qa_items(driver)
            
            if qa_items:
                print(f"\n成功提取 {len(qa_items)} 条QA")
                
                # 清空旧数据并添加新数据
                self.db.clear()
                for qa in qa_items:
                    self.db.add_qa(qa)
                
                # 保存到文件
                self.db.save()
                
                print("\n" + "="*50)
                print(f"✓ 爬取完成！共 {self.db.count()} 条QA")
                print(f"✓ 数据已保存到: {self.db.data_file}")
                print("="*50)
            else:
                print("\n未提取到QA数据")
                print(f"请检查 {DEBUG_HTML_FILE} 文件查看页面结构")
        
        except Exception as e:
            print(f"爬取失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()


def scrape_official_faq(headless=True, data_file=DEFAULT_DATA_FILE):
    """
    爬取官方FAQ的便捷函数
    
    Args:
        headless: 是否使用无头模式（默认True）
        data_file: 数据文件路径
    
    Returns:
        FAQDatabase: FAQ数据库对象
    
    Example:
        # 爬取FAQ
        db = scrape_official_faq()
        
        # 显示浏览器窗口
        db = scrape_official_faq(headless=False)
    """
    scraper = DigimonFAQScraper(headless=headless, data_file=data_file)
    scraper.scrape_faq()
    return scraper.db


def main():
    print("数码兽卡牌官方QA爬虫")
    print("=" * 50)
    
    # headless=False 显示浏览器窗口，便于调试
    scraper = DigimonFAQScraper(headless=False)
    scraper.scrape_faq()


if __name__ == "__main__":
    main()
