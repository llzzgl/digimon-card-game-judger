"""
数码兽卡牌官方QA完整爬虫
支持翻页，爬取所有238条QA
"""

import json
import time
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class DigimonFAQCompleteScraper:
    """完整的FAQ爬虫，支持翻页和增量保存"""
    
    def __init__(self, headless=True, output_file='official_qa_complete.json'):
        self.base_url = "https://app.digicamoe.cn/faq"
        self.headless = headless
        self.output_file = output_file
        self.existing_ids = set()
        self.load_existing_data()
        
    def load_existing_data(self):
        """加载已有数据，获取已存在的ID"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.existing_ids = {qa['id'] for qa in data if 'id' in qa}
                print(f"✓ 已加载 {len(self.existing_ids)} 条已有QA")
            except Exception as e:
                print(f"⚠ 加载已有数据失败: {e}")
                self.existing_ids = set()
        else:
            print(f"✓ 将创建新文件: {self.output_file}")
            # 创建空文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def add_qa_to_file(self, qa):
        """将单条QA追加到文件末尾"""
        # 检查是否已存在
        if qa['id'] in self.existing_ids:
            return False
        
        # 读取现有数据
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
        
        # 追加新数据
        data.append(qa)
        
        # 保存回文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 更新已存在ID集合
        self.existing_ids.add(qa['id'])
        return True
        
    def setup_driver(self):
        """设置浏览器"""
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
    
    def parse_qa_from_text(self, text):
        """从文本中解析QA"""
        qa_list = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('Q') and '：' in line:
                q_match = re.match(r'Q(\d+\.\d+)：(.+)', line)
                if q_match:
                    q_num = q_match.group(1)
                    question = q_match.group(2)
                    
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.startswith(f'A{q_num}：'):
                            answer = next_line.replace(f'A{q_num}：', '').strip()
                            
                            category = ""
                            if i + 2 < len(lines) and not lines[i + 2].startswith(('Q', 'A', '总共', '1', '2', '3')):
                                category = lines[i + 2].strip()
                            
                            qa_list.append({
                                'id': f'Q{q_num}',
                                'question': question,
                                'answer': answer,
                                'category': category,
                                'source': 'digicamoe_faq',
                                'url': self.base_url,
                                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
        
        return qa_list
    
    def click_next_page(self, driver):
        """点击下一页"""
        try:
            # 滚动到页面底部，确保分页按钮可见
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 查找下一页按钮
            next_buttons = driver.find_elements(By.CSS_SELECTOR, "li.ant-pagination-next")
            for btn in next_buttons:
                if 'ant-pagination-disabled' not in btn.get_attribute('class'):
                    try:
                        # 方法1: 使用JavaScript点击（更可靠）
                        driver.execute_script("arguments[0].click();", btn)
                        print("  ✓ 已点击下一页")
                    except:
                        # 方法2: 普通点击
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.5)
                        btn.click()
                        print("  ✓ 已点击下一页")
                    
                    time.sleep(4)  # 等待页面加载
                    
                    # 滚动到页面顶部
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    
                    return True
            
            print("  ⚠ 未找到可用的下一页按钮")
            return False
            
        except Exception as e:
            print(f"  ⚠ 翻页失败: {str(e)[:100]}")
            return False
    
    def scrape_all_pages(self):
        """爬取所有页面"""
        driver = self.setup_driver()
        
        try:
            print(f"正在访问: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)
            
            page = 1
            max_pages = 20  # 安全限制
            total_new = 0
            total_skipped = 0
            failed_pages = []
            
            while page <= max_pages:
                print(f"\n{'='*60}")
                print(f"第 {page} 页")
                print(f"{'='*60}")
                
                # 滚动页面，确保内容加载
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # 获取当前页面文本
                body = driver.find_element(By.TAG_NAME, 'body')
                page_text = body.text
                
                # 保存调试信息（仅在未提取到QA时）
                qa_list = self.parse_qa_from_text(page_text)
                
                if not qa_list:
                    # 保存页面HTML用于调试
                    debug_file = f"debug_page_{page}.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"  ⚠ 未提取到QA，已保存调试文件: {debug_file}")
                    
                    # 保存页面文本
                    debug_text_file = f"debug_page_{page}.txt"
                    with open(debug_text_file, "w", encoding="utf-8") as f:
                        f.write(page_text)
                    print(f"  ⚠ 页面文本已保存: {debug_text_file}")
                    print(f"  ⚠ 页面文本长度: {len(page_text)} 字符")
                    
                    failed_pages.append(page)
                
                if qa_list:
                    print(f"✓ 本页提取 {len(qa_list)} 条QA")
                    
                    # 逐条检查并保存
                    page_new = 0
                    page_skipped = 0
                    
                    for qa in qa_list:
                        if self.add_qa_to_file(qa):
                            page_new += 1
                            total_new += 1
                            print(f"  ✓ 新增: {qa['id']} - {qa['question'][:40]}...")
                        else:
                            page_skipped += 1
                            total_skipped += 1
                            print(f"  ⏭ 跳过: {qa['id']} (已存在)")
                    
                    print(f"\n本页统计: 新增 {page_new} 条, 跳过 {page_skipped} 条")
                    print(f"总计: 已保存 {len(self.existing_ids)} 条QA")
                else:
                    print("✗ 本页未提取到QA")
                
                # 尝试点击下一页
                if not self.click_next_page(driver):
                    print("\n已到最后一页")
                    break
                
                page += 1
            
            print(f"\n{'='*60}")
            print(f"✓ 爬取完成！")
            print(f"✓ 新增 {total_new} 条QA")
            print(f"✓ 跳过 {total_skipped} 条已存在QA")
            print(f"✓ 总计 {len(self.existing_ids)} 条QA")
            print(f"✓ 数据已保存到: {self.output_file}")
            
            if failed_pages:
                print(f"\n⚠ 以下页面未能提取QA: {failed_pages}")
                print(f"  已保存调试文件，可以手动检查")
            
            print(f"{'='*60}")
            
            # 统计分类
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    all_qa = json.load(f)
                
                categories = {}
                for qa in all_qa:
                    cat = qa.get('category', '未分类')
                    if cat:
                        categories[cat] = categories.get(cat, 0) + 1
                
                if categories:
                    print("\n分类统计:")
                    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
                        print(f"  {cat}: {count} 条")
            except:
                pass
        
        except Exception as e:
            print(f"\n❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()


def main():
    print("=" * 60)
    print("数码兽卡牌官方QA完整爬虫")
    print("=" * 60)
    
    scraper = DigimonFAQCompleteScraper(headless=True)
    scraper.scrape_all_pages()


if __name__ == "__main__":
    main()
