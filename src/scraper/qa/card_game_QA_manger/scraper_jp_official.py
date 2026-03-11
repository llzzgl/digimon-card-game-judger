"""
数码兽卡牌日文官网QA爬虫
从 https://digimoncard.com/rule/#qaResult_card 爬取日文QA
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


class JapaneseOfficialQAScraper:
    """日文官网QA爬虫"""
    
    def __init__(self, headless=True, output_file='official_qa_jp.json'):
        self.base_url = "https://digimoncard.com/rule/#qaResult_card"
        self.headless = headless
        self.output_file = output_file
        self.existing_ids = set()
        self.load_existing_data()
        
    def load_existing_data(self):
        """加载已有数据"""
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
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def setup_driver(self):
        """设置浏览器"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=ja')  # 设置日语
        
        try:
            print("启动Chrome...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✓ Chrome启动成功")
        return driver
    
    def get_prodid_options(self, driver):
        """获取所有収録弾選択的选项"""
        try:
            select_element = driver.find_element(By.NAME, 'prodid')
            options = select_element.find_elements(By.TAG_NAME, 'option')
            
            prodid_list = []
            for option in options:
                value = option.get_attribute('value')
                text = option.text.strip()
                if value:  # 跳过空值（"収録弾選択"）
                    prodid_list.append({
                        'value': value,
                        'text': text
                    })
            
            return prodid_list
        except Exception as e:
            print(f"获取选项失败: {e}")
            return []
    
    def search_by_prodid(self, driver, prodid_value):
        """根据prodid搜索QA"""
        try:
            # 选择prodid
            select_element = driver.find_element(By.NAME, 'prodid')
            driver.execute_script(f"arguments[0].value='{prodid_value}';", select_element)
            time.sleep(0.5)
            
            # 点击检索按钮
            search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            for btn in search_buttons:
                try:
                    # 检查按钮是否在卡片搜索表单中
                    form = btn.find_element(By.XPATH, './ancestor::form')
                    if 'qaResult_card' in form.get_attribute('action'):
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"  ✓ 已点击检索按钮")
                        time.sleep(5)  # 等待结果加载
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"  ✗ 搜索失败: {e}")
            return False
    
    def add_qa_to_file(self, qa):
        """将单条QA追加到文件"""
        if qa['id'] in self.existing_ids:
            return False
        
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
        
        data.append(qa)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.existing_ids.add(qa['id'])
        return True
    
    def has_next_page(self, driver):
        """检查是否有下一页"""
        try:
            # 查找当前页按钮
            current_page = driver.find_element(By.CSS_SELECTOR, '.pageBtn.current')
            
            # 查找当前页的下一个pageBtn
            try:
                next_page = current_page.find_element(By.XPATH, './following-sibling::li[@class="pageBtn"][1]')
                return next_page
            except:
                return None
        except:
            return None
    
    def click_next_page(self, driver):
        """点击下一页"""
        try:
            next_btn = self.has_next_page(driver)
            if next_btn:
                # 滚动到按钮位置
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(0.5)
                
                # 使用JavaScript点击
                driver.execute_script("arguments[0].click();", next_btn)
                print(f"    ✓ 已点击下一页")
                time.sleep(4)  # 等待页面加载
                
                # 滚动到顶部
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                return True
            return False
        except Exception as e:
            print(f"    ⚠ 翻页失败: {str(e)[:50]}")
            return False
    
    def scrape_prodid_all_pages(self, driver, prod):
        """爬取单个収録弾的所有页面"""
        # 滚动页面确保内容加载
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 提取QA（所有QA都在一页上）
        qa_list = self.extract_qa_items(driver)
        
        if not qa_list:
            print(f"  ✗ 未提取到QA")
            return 0
        
        print(f"  ✓ 提取到 {len(qa_list)} 条QA")
        
        # 逐条保存
        new_count = 0
        skip_count = 0
        
        for qa in qa_list:
            qa_id = qa['qa_number']  # 直接使用QA编号
            
            # 如果ID已存在，跳过
            if qa_id in self.existing_ids:
                skip_count += 1
                continue
            
            # 添加収録弾信息
            qa['id'] = qa_id
            qa['prodid'] = prod['value']
            qa['prod_name'] = prod['text']
            
            # 保存到文件
            if self.add_qa_to_file(qa):
                new_count += 1
                print(f"    ✓ 新增: {qa['qa_number']} - {qa['question'][:50]}...")
            else:
                skip_count += 1
        
        print(f"  统计: 新增 {new_count} 条, 跳过 {skip_count} 条")
        return new_count
    
    def extract_qa_items(self, driver):
        """提取QA条目"""
        qa_list = []
        
        try:
            # 等待QA结果加载
            time.sleep(2)
            
            # 查找所有qa_box（每个box包含卡牌信息和QA）
            qa_boxes = driver.find_elements(By.CSS_SELECTOR, 'dl.qa_box')
            
            if not qa_boxes:
                print("  未找到QA元素")
                return qa_list
            
            print(f"  找到 {len(qa_boxes)} 个qa_box")
            
            # 遍历每个qa_box
            for box in qa_boxes:
                try:
                    # 提取卡牌信息（第一个dt.qa_category）
                    card_no = None
                    card_name = None
                    
                    try:
                        card_dt = box.find_element(By.CSS_SELECTOR, 'dt.qa_category')
                        card_info = card_dt.text.strip()
                        
                        # 如果text为空，尝试使用innerHTML
                        if not card_info:
                            card_html = card_dt.get_attribute('innerHTML')
                            # 简单的HTML标签去除
                            card_info = re.sub(r'<[^>]+>', '', card_html).strip()
                        
                        # 解析卡牌编号和名称（格式：EX11-001 コロモン）
                        if card_info:
                            parts = card_info.split(' ', 1)
                            if len(parts) >= 1:
                                card_no = parts[0].strip()
                            if len(parts) >= 2:
                                card_name = parts[1].strip()
                            print(f"    [DEBUG] 提取到卡牌信息: {card_no} {card_name}")
                    except Exception as e:
                        # 这个box没有卡牌信息（可能是通用规则QA）
                        pass
                    
                    # 查找box内的所有questions
                    questions = box.find_elements(By.CSS_SELECTOR, 'dl.questions')
                    
                    # 如果这个box没有questions，跳过
                    if not questions:
                        continue
                    
                    for q_dl in questions:
                        try:
                            # 提取问题 - 使用innerHTML而不是text，因为有些元素不可见
                            q_dt = q_dl.find_element(By.TAG_NAME, 'dt')
                            q_dd = q_dl.find_element(By.TAG_NAME, 'dd')
                            
                            # 优先使用text，如果为空则使用innerHTML
                            q_number = q_dt.text.strip()
                            if not q_number:
                                q_number = q_dt.get_attribute('innerHTML').strip()
                            
                            q_content = q_dd.text.strip()
                            if not q_content:
                                # 从innerHTML提取文本（去除HTML标签）
                                import re
                                q_html = q_dd.get_attribute('innerHTML')
                                # 简单的HTML标签去除
                                q_content = re.sub(r'<[^>]+>', '\n', q_html).strip()
                                q_content = re.sub(r'\n+', '\n', q_content)
                            
                            # 查找对应的答案（下一个answer元素）
                            try:
                                a_dl = q_dl.find_element(By.XPATH, './following-sibling::dl[@class="answer"][1]')
                                a_dt = a_dl.find_element(By.TAG_NAME, 'dt')
                                a_dd = a_dl.find_element(By.TAG_NAME, 'dd')
                                
                                # 优先使用text，如果为空则使用innerHTML
                                a_number = a_dt.text.strip()
                                if not a_number:
                                    a_number = a_dt.get_attribute('innerHTML').strip()
                                
                                a_content = a_dd.text.strip()
                                if not a_content:
                                    # 从innerHTML提取文本
                                    a_html = a_dd.get_attribute('innerHTML')
                                    a_content = re.sub(r'<[^>]+>', '\n', a_html).strip()
                                    a_content = re.sub(r'\n+', '\n', a_content)
                                
                                # 提取QA编号（去掉Q/A前缀）
                                qa_number = re.sub(r'^[QA]', '', q_number)
                                
                                # 跳过没有编号的QA
                                if not qa_number or not qa_number.strip():
                                    continue
                                
                                qa_item = {
                                    'id': qa_number,  # 直接使用QA编号作为ID
                                    'question': q_content,
                                    'answer': a_content,
                                    'qa_number': qa_number,
                                    'language': 'ja',
                                    'source': 'digimoncard.com',
                                    'url': self.base_url,
                                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # 添加卡牌信息（如果有）
                                if card_no:
                                    qa_item['card_no'] = card_no
                                if card_name:
                                    qa_item['card_name'] = card_name
                                
                                qa_list.append(qa_item)
                            
                            except Exception as e:
                                # 如果找不到答案，跳过这个问题
                                continue
                        
                        except Exception as e:
                            continue
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"  提取QA失败: {e}")
        
        return qa_list
    
    def parse_qa_from_text(self, text):
        """从文本中解析QA（日文格式）"""
        qa_list = []
        
        # 日文QA通常使用 Q: 和 A: 或 Q. 和 A.
        lines = text.split('\n')
        
        i = 0
        qa_index = 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 匹配日文Q&A格式
            if line.startswith(('Q:', 'Q：', 'Q.', 'Ｑ：', 'Ｑ.')):
                question = re.sub(r'^[QＱ][：:.]', '', line).strip()
                
                # 查找答案
                answer_lines = []
                j = i + 1
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    if next_line.startswith(('A:', 'A：', 'A.', 'Ａ：', 'Ａ.')):
                        answer = re.sub(r'^[AＡ][：:.]', '', next_line).strip()
                        answer_lines.append(answer)
                        j += 1
                        
                        # 继续读取多行答案
                        while j < len(lines):
                            cont_line = lines[j].strip()
                            if cont_line and not cont_line.startswith(('Q', 'Ｑ', 'A', 'Ａ')):
                                answer_lines.append(cont_line)
                                j += 1
                            else:
                                break
                        break
                    j += 1
                
                if answer_lines:
                    qa_id = f"JP_Q{qa_index}"
                    
                    qa_list.append({
                        'id': qa_id,
                        'question': question,
                        'answer': '\n'.join(answer_lines),
                        'language': 'ja',
                        'source': 'digimoncard.com',
                        'url': self.base_url,
                        'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    qa_index += 1
                    i = j
                    continue
            
            i += 1
        
        return qa_list
    
    def scrape(self):
        """执行爬取"""
        driver = self.setup_driver()
        
        try:
            print(f"\n正在访问: {self.base_url}")
            driver.get(self.base_url)
            
            # 等待页面加载
            time.sleep(8)
            
            # 获取所有収録弾選択选项
            print("\n获取収録弾選択列表...")
            prodid_options = self.get_prodid_options(driver)
            
            if not prodid_options:
                print("❌ 未找到収録弾選択选项")
                return
            
            print(f"✓ 找到 {len(prodid_options)} 个収録弾")
            
            # 遍历每个収録弾
            total_new = 0
            total_skip = 0
            
            for idx, prod in enumerate(prodid_options, 1):
                print(f"\n{'='*60}")
                print(f"[{idx}/{len(prodid_options)}] {prod['text']}")
                print(f"{'='*60}")
                
                # 搜索该収録弾的QA
                if not self.search_by_prodid(driver, prod['value']):
                    print("  ✗ 搜索失败，跳过")
                    continue
                
                # 爬取该収録弾的所有页面
                prod_total = self.scrape_prodid_all_pages(driver, prod)
                
                if prod_total > 0:
                    print(f"  本弹总计: {prod_total} 条QA")
                    total_new += prod_total
                else:
                    print(f"  本弹未提取到QA")
                
                # 保存当前进度
                print(f"  累计总计: {len(self.existing_ids)} 条QA")
            
            # 最终统计
            print(f"\n{'='*60}")
            print(f"✓ 爬取完成！")
            print(f"✓ 新增 {total_new} 条QA")
            print(f"✓ 总计 {len(self.existing_ids)} 条QA")
            print(f"✓ 数据已保存到: {self.output_file}")
            print(f"{'='*60}")
            
            # 统计収録弾分布
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    all_qa = json.load(f)
                
                prod_stats = {}
                for qa in all_qa:
                    prod_name = qa.get('prod_name', '未知')
                    prod_stats[prod_name] = prod_stats.get(prod_name, 0) + 1
                
                if prod_stats:
                    print("\n収録弾统计（前10）:")
                    for prod, count in sorted(prod_stats.items(), key=lambda x: -x[1])[:10]:
                        print(f"  {prod}: {count} 条")
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
    print("数码兽卡牌日文官网QA爬虫")
    print("=" * 60)
    
    scraper = JapaneseOfficialQAScraper(headless=False)  # 显示浏览器便于调试
    scraper.scrape()


if __name__ == "__main__":
    main()
