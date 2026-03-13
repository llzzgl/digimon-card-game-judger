"""
QA 爬虫统一接口
整合日文和中文 QA 爬取功能
"""
import json
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QAScraper:
    """
    QA 爬虫统一接口
    爬取官方 Q&A 裁定数据
    """
    
    def __init__(self, config: dict = None):
        """
        初始化 QA 爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.output_path = Path(self.config.get("output_path", "rulings.json"))
        self.headless = self.config.get("headless", True)
        self.driver = None
        self.qa_list = []
        self.existing_ids = set()
        
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
        chrome_options.add_argument('--lang=ja')
        
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
        """加载已有数据"""
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.qa_list = data if isinstance(data, list) else []
                    self.existing_ids = {qa.get('id') or qa.get('qa_number') for qa in self.qa_list}
                logger.info(f"✓ 已加载 {len(self.existing_ids)} 条已有 QA")
            except Exception as e:
                logger.error(f"加载已有数据失败：{e}")
                self.qa_list = []
                self.existing_ids = set()
        else:
            logger.info(f"✓ 将创建新文件：{self.output_path}")
    
    def scrape_japanese_official(self, output_path: Path = None) -> int:
        """
        爬取日文官网 QA
        
        Args:
            output_path: 输出路径
            
        Returns:
            新增 QA 数量
        """
        logger.info("\n" + "="*60)
        logger.info("开始爬取日文官网 QA")
        logger.info("="*60)
        
        if output_path:
            self.output_path = output_path
        
        self.load_existing_data()
        
        if not self.driver:
            self.setup()
        
        try:
            base_url = "https://digimoncard.com/rule/#qaResult_card"
            logger.info(f"访问：{base_url}")
            self.driver.get(base_url)
            time.sleep(5)
            
            # 获取所有収録弾选项
            prodid_options = self._get_prodid_options()
            logger.info(f"找到 {len(prodid_options)} 个卡包分类")
            
            new_count = 0
            
            for idx, prod in enumerate(prodid_options, 1):
                logger.info(f"\n[{idx}/{len(prodid_options)}] 爬取：{prod['text']}")
                
                # 搜索该分类的 QA
                self._search_by_prodid(prod['value'])
                time.sleep(3)
                
                # 提取 QA
                qa_items = self._extract_qa_items()
                logger.info(f"  提取到 {len(qa_items)} 条 QA")
                
                # 保存新 QA
                for qa in qa_items:
                    qa_id = qa.get('qa_number') or qa.get('id')
                    if qa_id and qa_id not in self.existing_ids:
                        self.qa_list.append(qa)
                        self.existing_ids.add(qa_id)
                        new_count += 1
                        logger.debug(f"    ✓ 新增 QA: {qa_id}")
                
                # 延迟避免请求过快
                time.sleep(2)
            
            # 保存数据
            self._save_data()
            logger.info(f"\n✓ 日文官网 QA 爬取完成，新增 {new_count} 条")
            return new_count
            
        except Exception as e:
            logger.error(f"爬取失败：{e}")
            return 0
        finally:
            self.close()
    
    def _get_prodid_options(self) -> List[Dict]:
        """获取所有収録弾選択选项"""
        from selenium.webdriver.common.by import By
        
        try:
            select_element = self.driver.find_element(By.NAME, 'prodid')
            options = select_element.find_elements(By.TAG_NAME, 'option')
            
            prodid_list = []
            for option in options:
                value = option.get_attribute('value')
                text = option.text.strip()
                if value:  # 跳过空值
                    prodid_list.append({'value': value, 'text': text})
            
            return prodid_list
        except Exception as e:
            logger.error(f"获取选项失败：{e}")
            return []
    
    def _search_by_prodid(self, prodid_value: str):
        """根据 prodid 搜索 QA"""
        from selenium.webdriver.common.by import By
        
        try:
            select_element = self.driver.find_element(By.NAME, 'prodid')
            self.driver.execute_script(f"arguments[0].value='{prodid_value}';", select_element)
            time.sleep(0.5)
            
            # 点击检索按钮
            search_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            for btn in search_buttons:
                try:
                    form = btn.find_element(By.XPATH, './ancestor::form')
                    if form and 'qaResult_card' in form.get_attribute('action'):
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.debug("  ✓ 已点击检索按钮")
                        time.sleep(5)
                        return
                except:
                    continue
        except Exception as e:
            logger.error(f"  ✗ 搜索失败：{e}")
    
    def _extract_qa_items(self) -> List[Dict]:
        """提取 QA 列表"""
        from selenium.webdriver.common.by import By
        
        qa_items = []
        
        try:
            # 查找 QA 项
            qa_elements = self.driver.find_elements(By.CSS_SELECTOR, ".qa_item, .qalist_item, [class*='qa']")
            
            for elem in qa_elements:
                try:
                    qa = self._parse_qa_element(elem)
                    if qa:
                        qa_items.append(qa)
                except Exception as e:
                    logger.debug(f"    解析 QA 失败：{e}")
        except Exception as e:
            logger.error(f"提取 QA 失败：{e}")
        
        return qa_items
    
    def _parse_qa_element(self, elem) -> Optional[Dict]:
        """解析单个 QA 元素"""
        from selenium.webdriver.common.by import By
        
        try:
            qa = {}
            
            # QA 编号
            try:
                num_elem = elem.find_element(By.CSS_SELECTOR, ".qa_number, .qano, [class*='number']")
                qa['qa_number'] = num_elem.text.strip()
            except:
                qa['qa_number'] = ""
            
            # 问题
            try:
                q_elem = elem.find_element(By.CSS_SELECTOR, ".question, .q_text, [class*='question']")
                qa['question'] = q_elem.text.strip()
            except:
                qa['question'] = ""
            
            # 答案
            try:
                a_elem = elem.find_element(By.CSS_SELECTOR, ".answer, .a_text, [class*='answer']")
                qa['answer'] = a_elem.text.strip()
            except:
                qa['answer'] = ""
            
            # 卡牌编号
            try:
                card_elem = elem.find_element(By.CSS_SELECTOR, ".card_no, .cardno")
                qa['card_no'] = card_elem.text.strip()
            except:
                qa['card_no'] = ""
            
            # 卡牌名称
            try:
                name_elem = elem.find_element(By.CSS_SELECTOR, ".card_name, .cardname")
                qa['card_name'] = name_elem.text.strip()
            except:
                qa['card_name'] = ""
            
            # 分类
            try:
                cat_elem = elem.find_element(By.CSS_SELECTOR, ".category, .category_name")
                qa['category'] = cat_elem.text.strip()
            except:
                qa['category'] = ""
            
            # 添加元数据
            qa['id'] = qa['qa_number']  # 使用 QA 编号作为 ID
            qa['language'] = 'ja'
            qa['scraped_at'] = datetime.now().isoformat()
            
            return qa
        except Exception as e:
            logger.debug(f"解析 QA 元素失败：{e}")
            return None
    
    def _save_data(self):
        """保存数据到文件"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.qa_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ 数据已保存到：{self.output_path}")
    
    def scrape_faq(self, output_path: Path = None) -> int:
        """
        爬取 FAQ（待实现）
        
        Args:
            output_path: 输出路径
            
        Returns:
            新增 QA 数量
        """
        logger.info("FAQ 爬取功能待实现")
        return 0
    
    def search_qa(self, keyword: str) -> List[Dict]:
        """
        搜索 QA
        
        Args:
            keyword: 关键词
            
        Returns:
            匹配的 QA 列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for qa in self.qa_list:
            question = qa.get('question', '').lower()
            answer = qa.get('answer', '').lower()
            card_name = qa.get('card_name', '').lower()
            
            if keyword_lower in question or keyword_lower in answer or keyword_lower in card_name:
                results.append(qa)
        
        logger.info(f"搜索 '{keyword}' 找到 {len(results)} 条结果")
        return results
    
    def get_qa_by_card(self, card_no: str) -> List[Dict]:
        """
        根据卡牌编号获取相关 QA
        
        Args:
            card_no: 卡牌编号
            
        Returns:
            QA 列表
        """
        results = []
        
        for qa in self.qa_list:
            if qa.get('card_no') == card_no:
                results.append(qa)
        
        logger.info(f"卡牌 {card_no} 有 {len(results)} 条 QA")
        return results
    
    def validate_qa(self) -> Dict:
        """
        验证 QA 数据
        
        Returns:
            验证报告
        """
        report = {
            'total': len(self.qa_list),
            'valid': 0,
            'invalid': 0,
            'missing_fields': {},
            'errors': []
        }
        
        required_fields = ['id', 'question', 'answer']
        
        for qa in self.qa_list:
            is_valid = True
            
            for field in required_fields:
                if not qa.get(field):
                    is_valid = False
                    if field not in report['missing_fields']:
                        report['missing_fields'][field] = 0
                    report['missing_fields'][field] += 1
            
            if is_valid:
                report['valid'] += 1
            else:
                report['invalid'] += 1
                report['errors'].append({
                    'id': qa.get('id', 'UNKNOWN'),
                    'missing': [f for f in required_fields if not qa.get(f)]
                })
        
        logger.info(f"验证完成：{report['valid']} 有效 / {report['invalid']} 无效")
        return report
