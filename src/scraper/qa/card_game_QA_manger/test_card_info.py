"""
测试卡牌信息提取
只爬取第一个収録弾，检查卡牌信息是否正确保存
"""

import json
import time
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    """设置浏览器"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    
    try:
        print("启动Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    print("✓ Chrome启动成功")
    return driver


def extract_qa_items(driver):
    """提取QA条目"""
    qa_list = []
    
    try:
        time.sleep(2)
        
        qa_boxes = driver.find_elements(By.CSS_SELECTOR, 'dl.qa_box')
        
        if not qa_boxes:
            print("  未找到QA元素")
            return qa_list
        
        print(f"  找到 {len(qa_boxes)} 个qa_box")
        
        for box_idx, box in enumerate(qa_boxes[:3], 1):  # 只测试前3个box
            try:
                # 提取卡牌信息
                card_no = None
                card_name = None
                
                try:
                    card_dt = box.find_element(By.CSS_SELECTOR, 'dt.qa_category')
                    card_info = card_dt.text.strip()
                    
                    # 如果text为空，尝试使用innerHTML
                    if not card_info:
                        card_html = card_dt.get_attribute('innerHTML')
                        card_info = re.sub(r'<[^>]+>', '', card_html).strip()
                    
                    # 解析卡牌编号和名称
                    if card_info:
                        parts = card_info.split(' ', 1)
                        if len(parts) >= 1:
                            card_no = parts[0].strip()
                        if len(parts) >= 2:
                            card_name = parts[1].strip()
                        print(f"    Box {box_idx} - 卡牌信息: {card_no} {card_name}")
                    else:
                        print(f"    Box {box_idx} - 无卡牌信息（通用规则QA）")
                except Exception as e:
                    print(f"    Box {box_idx} - 无卡牌信息: {e}")
                
                # 查找box内的所有questions
                questions = box.find_elements(By.CSS_SELECTOR, 'dl.questions')
                
                if not questions:
                    continue
                
                print(f"    Box {box_idx} - 找到 {len(questions)} 个问题")
                
                for q_idx, q_dl in enumerate(questions[:2], 1):  # 每个box只测试前2个QA
                    try:
                        q_dt = q_dl.find_element(By.TAG_NAME, 'dt')
                        q_dd = q_dl.find_element(By.TAG_NAME, 'dd')
                        
                        q_number = q_dt.text.strip()
                        if not q_number:
                            q_number = q_dt.get_attribute('innerHTML').strip()
                        
                        q_content = q_dd.text.strip()
                        if not q_content:
                            q_html = q_dd.get_attribute('innerHTML')
                            q_content = re.sub(r'<[^>]+>', '\n', q_html).strip()
                            q_content = re.sub(r'\n+', '\n', q_content)
                        
                        try:
                            a_dl = q_dl.find_element(By.XPATH, './following-sibling::dl[@class="answer"][1]')
                            a_dt = a_dl.find_element(By.TAG_NAME, 'dt')
                            a_dd = a_dl.find_element(By.TAG_NAME, 'dd')
                            
                            a_number = a_dt.text.strip()
                            if not a_number:
                                a_number = a_dt.get_attribute('innerHTML').strip()
                            
                            a_content = a_dd.text.strip()
                            if not a_content:
                                a_html = a_dd.get_attribute('innerHTML')
                                a_content = re.sub(r'<[^>]+>', '\n', a_html).strip()
                                a_content = re.sub(r'\n+', '\n', a_content)
                            
                            qa_number = re.sub(r'^[QA]', '', q_number)
                            
                            if not qa_number or not qa_number.strip():
                                continue
                            
                            qa_item = {
                                'id': qa_number,
                                'question': q_content[:50] + '...',
                                'answer': a_content[:50] + '...',
                                'qa_number': qa_number,
                                'language': 'ja',
                                'source': 'digimoncard.com',
                                'url': 'https://digimoncard.com/rule/#qaResult_card',
                                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # 添加卡牌信息
                            if card_no:
                                qa_item['card_no'] = card_no
                            if card_name:
                                qa_item['card_name'] = card_name
                            
                            qa_list.append(qa_item)
                            
                            print(f"      QA {q_idx}: {qa_number} - card_no={card_no}, card_name={card_name}")
                        
                        except Exception as e:
                            continue
                    
                    except Exception as e:
                        continue
            
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"  提取QA失败: {e}")
    
    return qa_list


def main():
    print("=" * 60)
    print("测试卡牌信息提取")
    print("=" * 60)
    
    driver = setup_driver()
    
    try:
        base_url = "https://digimoncard.com/rule/#qaResult_card"
        print(f"\n正在访问: {base_url}")
        driver.get(base_url)
        
        time.sleep(8)
        
        # 获取第一个収録弾
        select_element = driver.find_element(By.NAME, 'prodid')
        options = select_element.find_elements(By.TAG_NAME, 'option')
        
        first_prod = None
        for option in options:
            value = option.get_attribute('value')
            text = option.text.strip()
            if value:
                first_prod = {'value': value, 'text': text}
                break
        
        if not first_prod:
            print("❌ 未找到収録弾")
            return
        
        print(f"\n测试収録弾: {first_prod['text']}")
        
        # 选择并搜索
        driver.execute_script(f"arguments[0].value='{first_prod['value']}';", select_element)
        time.sleep(0.5)
        
        search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        for btn in search_buttons:
            try:
                form = btn.find_element(By.XPATH, './ancestor::form')
                if 'qaResult_card' in form.get_attribute('action'):
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"✓ 已点击检索按钮")
                    time.sleep(5)
                    break
            except:
                continue
        
        # 滚动页面
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 提取QA
        qa_list = extract_qa_items(driver)
        
        print(f"\n提取到 {len(qa_list)} 条QA")
        
        # 保存到测试文件
        output_file = 'test_card_info_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 已保存到: {output_file}")
        
        # 显示前3条QA
        print("\n前3条QA:")
        for qa in qa_list[:3]:
            print(f"\nQA {qa['qa_number']}:")
            print(f"  card_no: {qa.get('card_no', 'N/A')}")
            print(f"  card_name: {qa.get('card_name', 'N/A')}")
            print(f"  question: {qa['question']}")
            print(f"  answer: {qa['answer']}")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
