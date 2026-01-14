"""
数码宝贝卡牌爬虫脚本 v2
优化版：直接从列表页提取数据，避免逐个打开详情页
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
    """数码宝贝卡牌爬虫 v2"""
    
    BASE_URL = "https://digimoncard.com"
    CARDLIST_URL = f"{BASE_URL}/cards/"
    
    def __init__(self, headless: bool = True, output_dir: str = "output", chrome_driver_path: str = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=ja")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = None
        if chrome_driver_path:
            service = Service(executable_path=chrome_driver_path)
        elif USE_WEBDRIVER_MANAGER:
            try:
                service = Service(ChromeDriverManager().install())
            except:
                pass
        
        if service:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
            
        self.wait = WebDriverWait(self.driver, 20)
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def close(self):
        if self.driver:
            self.driver.quit()

    def get_cards_from_pack(self, pack: CardPack) -> List[Card]:
        """从卡包页面批量提取卡牌信息"""
        cards = []
        
        try:
            print(f"\n正在爬取卡包: {pack.pack_name}")
            self.driver.get(pack.pack_url)
            time.sleep(4)
            
            # 等待卡牌列表加载 - 尝试多个可能的选择器
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".image_lists, .cardlist, ul.image_lists")))
            except TimeoutException:
                print("  警告: 标准选择器未找到，尝试查找任何卡牌元素...")
            
            # 先检查页面状态
            page_info = self.driver.execute_script("""
                return {
                    allLinks: document.querySelectorAll('a[href*="card_no"]').length,
                    allLinksTotal: document.querySelectorAll('a').length,
                    allImages: document.querySelectorAll('img').length,
                    allLis: document.querySelectorAll('li').length,
                    sampleLink: document.querySelector('a') ? document.querySelector('a').href : '',
                    bodyText: document.body.innerText.substring(0, 200)
                };
            """)
            print(f"  页面状态: {page_info['allLinks']} 个卡牌链接 (共{page_info['allLinksTotal']}个链接), {page_info['allImages']} 张图片, {page_info['allLis']} 个li元素")
            if page_info['sampleLink']:
                print(f"  示例链接: {page_info['sampleLink'][:100]}")
            
            # 使用JavaScript一次性获取所有卡牌数据 - 包括详情
            card_data_list = self.driver.execute_script("""
                var cards = [];
                var debugInfo = {foundSelector: '', itemCount: 0, sampleHtml: ''};
                
                // 尝试多种可能的选择器
                var selectors = [
                    '.image_lists li',
                    '.cardlist_item',
                    '.card-item',
                    'ul.image_lists > li',
                    '.cardlist li',
                    'li[data-card-no]'
                ];
                
                var items = [];
                for (var i = 0; i < selectors.length; i++) {
                    items = document.querySelectorAll(selectors[i]);
                    if (items.length > 0) {
                        debugInfo.foundSelector = selectors[i];
                        debugInfo.itemCount = items.length;
                        if (items[0]) {
                            debugInfo.sampleHtml = items[0].outerHTML.substring(0, 300);
                        }
                        break;
                    }
                }
                
                items.forEach(function(item) {
                    var card = {};
                    
                    // 获取链接和卡号 - 更灵活的匹配
                    var link = item.querySelector('a');
                    if (link) {
                        card.url = link.href;
                        
                        // 获取 data-src 属性（指向详情内容的ID）
                        var dataSrc = link.getAttribute('data-src');
                        if (dataSrc) {
                            card.detail_id = dataSrc.replace('#', '');
                            // 如果 data-src 本身就是卡号格式，直接使用
                            if (!card.card_no && dataSrc.match(/[A-Z]{1,3}\d{0,2}-[A-Z0-9]{1,5}/)) {
                                card.card_no = dataSrc.replace('#', '');
                            }
                        }
                        
                        // 尝试多种URL模式
                        var patterns = [
                            /card_no=([A-Za-z0-9-]+)/,
                            /cardno=([A-Za-z0-9-]+)/i,
                            /card[_-]?id=([A-Za-z0-9-]+)/i,
                            /\/([A-Z]{1,3}\d{0,2}-[A-Z0-9]{1,5}[A-Z]?)$/,  // 从URL末尾提取
                            /\/([A-Z]{1,3}\d{0,2}-[A-Z0-9]{1,5}[A-Z]?)\//   // 从URL路径提取
                        ];
                        
                        for (var i = 0; i < patterns.length; i++) {
                            var match = link.href.match(patterns[i]);
                            if (match) {
                                card.card_no = match[1];
                                break;
                            }
                        }
                        
                        // 如果URL中没有，尝试从文本中提取
                        if (!card.card_no) {
                            var textMatch = link.textContent.match(/([A-Z]{1,3}\d{0,2}-[A-Z0-9]{1,5}[A-Z]?)/);
                            if (textMatch) {
                                card.card_no = textMatch[1];
                            }
                        }
                    }
                    
                    // 获取图片
                    var img = item.querySelector('img');
                    if (img) {
                        card.image_url = img.src;
                        card.card_name = img.alt || '';
                        
                        // 尝试从图片URL提取卡号 (优先，因为这个最准确)
                        if (!card.card_no) {
                            // 匹配多种格式：BT24-001, P-194, EX10-071, ST-18, BT24-TOKEN, etc.
                            var imgMatch = img.src.match(/([A-Z]{1,3}\d{0,2}-[A-Z0-9]{1,5}[A-Z]?)/);
                            if (imgMatch) {
                                card.card_no = imgMatch[1];
                            }
                        }
                    }
                    
                    // 尝试获取其他数据属性
                    var dataNo = item.getAttribute('data-no') || item.getAttribute('data-card-no') || 
                                 item.getAttribute('data-cardno') || '';
                    if (dataNo) {
                        card.card_no = card.card_no || dataNo;
                        card.data_no = dataNo;
                    }
                    
                    // 尝试从页面中的隐藏详情元素获取信息
                    if (card.detail_id) {
                        var detailDiv = document.getElementById(card.detail_id);
                        if (detailDiv) {
                            // 提取详情信息
                            var details = {};
                            
                            // 卡牌类型
                            var typeEl = detailDiv.querySelector('.cardType');
                            if (typeEl) details.card_type = typeEl.textContent.trim();
                            
                            // 稀有度
                            var rarityEl = detailDiv.querySelector('.cardRarity');
                            if (rarityEl) details.rarity = rarityEl.textContent.trim();
                            
                            // 等级
                            var lvEl = detailDiv.querySelector('.cardLv');
                            if (lvEl) {
                                var lvMatch = lvEl.textContent.match(/\\d+/);
                                if (lvMatch) details.level = parseInt(lvMatch[0]);
                            }
                            
                            // 颜色 - 从 cardColor span 中提取
                            var colorSpans = detailDiv.querySelectorAll('.cardColor span');
                            var colors = [];
                            colorSpans.forEach(function(span) {
                                var text = span.textContent.trim();
                                if (text && text !== '') {
                                    colors.push(text);
                                }
                            });
                            if (colors.length > 0) {
                                details.color = colors[0];
                                if (colors.length > 1) details.color2 = colors[1];
                            }
                            
                            // 费用 - 查找包含"コスト"的元素（不是進化コスト）
                            var costDt = Array.from(detailDiv.querySelectorAll('dt')).find(function(dt) {
                                var text = dt.textContent.trim();
                                return text === 'コスト' || text.includes('登場コスト');
                            });
                            if (costDt && costDt.nextElementSibling) {
                                var costMatch = costDt.nextElementSibling.textContent.match(/\\d+/);
                                if (costMatch) details.cost = parseInt(costMatch[0]);
                            }
                            
                            // DP
                            var dpDt = Array.from(detailDiv.querySelectorAll('dt')).find(function(dt) {
                                return dt.textContent.includes('DP');
                            });
                            if (dpDt && dpDt.nextElementSibling) {
                                var dpMatch = dpDt.nextElementSibling.textContent.match(/\\d+/);
                                if (dpMatch) details.dp = parseInt(dpMatch[0]);
                            }
                            
                            // 形态
                            var formDt = Array.from(detailDiv.querySelectorAll('dt')).find(function(dt) {
                                return dt.textContent.includes('形態');
                            });
                            if (formDt && formDt.nextElementSibling) {
                                details.form = formDt.nextElementSibling.textContent.trim();
                            }
                            
                            // 属性
                            var attrDt = Array.from(detailDiv.querySelectorAll('dt')).find(function(dt) {
                                return dt.textContent.includes('属性');
                            });
                            if (attrDt && attrDt.nextElementSibling) {
                                details.attribute = attrDt.nextElementSibling.textContent.trim();
                            }
                            
                            // 类型（数码宝贝类型）
                            var typeDt = Array.from(detailDiv.querySelectorAll('dt')).find(function(dt) {
                                return dt.textContent.includes('タイプ');
                            });
                            if (typeDt && typeDt.nextElementSibling) {
                                details.digimon_type = typeDt.nextElementSibling.textContent.trim();
                            }
                            
                            // 效果 - 查找包含"効果"的元素
                            var effectDt = Array.from(detailDiv.querySelectorAll('.cardInfoTitMedium, .cardInfoTitSmall')).find(function(dt) {
                                return dt.textContent.includes('効果');
                            });
                            if (effectDt) {
                                var effectDd = effectDt.nextElementSibling;
                                if (effectDd) {
                                    details.effect = effectDd.textContent.trim();
                                }
                            }
                            
                            // 进化源效果
                            var inheritedDt = Array.from(detailDiv.querySelectorAll('.cardInfoTitSmall')).find(function(dt) {
                                return dt.textContent.includes('進化元');
                            });
                            if (inheritedDt) {
                                var inheritedDd = inheritedDt.nextElementSibling;
                                if (inheritedDd) {
                                    details.inherited_effect = inheritedDd.textContent.trim();
                                }
                            }
                            
                            // 进化费用 - 查找包含"進化条件"的元素
                            var evolveDts = Array.from(detailDiv.querySelectorAll('dt')).filter(function(dt) {
                                return dt.textContent.includes('進化条件');
                            });
                            if (evolveDts.length > 0) {
                                // 第一个进化条件
                                var evolveDd1 = evolveDts[0].nextElementSibling;
                                if (evolveDd1) {
                                    var evolveText1 = evolveDd1.textContent;
                                    // 提取进化费用数字（最后的数字）
                                    var costMatches1 = evolveText1.match(/\\d+/g);
                                    if (costMatches1 && costMatches1.length > 0) {
                                        details.digivolve_cost1 = parseInt(costMatches1[costMatches1.length - 1]);
                                    }
                                    // 提取进化颜色
                                    var colorSpans1 = evolveDd1.querySelectorAll('span[class*="cardColor_"]');
                                    if (colorSpans1.length > 0) {
                                        var colors1 = [];
                                        colorSpans1.forEach(function(span) {
                                            var text = span.textContent.trim();
                                            if (text && text !== '') {
                                                colors1.push(text);
                                            }
                                        });
                                        if (colors1.length > 0) {
                                            details.digivolve_color1 = colors1.join('/');
                                        }
                                    }
                                }
                                
                                // 第二个进化条件
                                if (evolveDts.length > 1) {
                                    var evolveDd2 = evolveDts[1].nextElementSibling;
                                    if (evolveDd2) {
                                        var evolveText2 = evolveDd2.textContent;
                                        var costMatches2 = evolveText2.match(/\\d+/g);
                                        if (costMatches2 && costMatches2.length > 0) {
                                            details.digivolve_cost2 = parseInt(costMatches2[costMatches2.length - 1]);
                                        }
                                        var colorSpans2 = evolveDd2.querySelectorAll('span[class*="cardColor_"]');
                                        if (colorSpans2.length > 0) {
                                            var colors2 = [];
                                            colorSpans2.forEach(function(span) {
                                                var text = span.textContent.trim();
                                                if (text && text !== '') {
                                                    colors2.push(text);
                                                }
                                            });
                                            if (colors2.length > 0) {
                                                details.digivolve_color2 = colors2.join('/');
                                            }
                                        }
                                    }
                                }
                            }
                            
                            card.details = details;
                        } else {
                            // 如果找不到详情div，标记为缺失详情
                            card.missing_details = true;
                        }
                    }
                    
                    // 只要有卡号或图片URL就认为是有效卡牌
                    if (card.card_no || card.image_url) {
                        cards.push(card);
                    }
                });
                
                return {cards: cards, debug: debugInfo};
            """)
            
            debug_info = card_data_list.get('debug', {})
            card_data_list = card_data_list.get('cards', [])
            
            if debug_info:
                print(f"  调试信息: 使用选择器 '{debug_info.get('foundSelector', 'unknown')}' 找到 {debug_info.get('itemCount', 0)} 个元素")
                if debug_info.get('sampleHtml'):
                    print(f"  示例HTML: {debug_info['sampleHtml'][:200]}...")
            
            print(f"发现 {len(card_data_list)} 张卡牌，开始处理...")
            
            # 批量处理卡牌
            skipped_count = 0
            missing_details_count = 0
            for idx, data in enumerate(card_data_list):
                card_no = data.get('card_no') or data.get('data_no') or ''
                card_name = data.get('card_name', '')
                image_url = data.get('image_url', '')
                card_url = data.get('url', '')
                details = data.get('details', {})
                missing_details = data.get('missing_details', False)
                
                if not card_no:
                    skipped_count += 1
                    if skipped_count <= 3:  # 只打印前3个被跳过的卡牌
                        print(f"  警告: 跳过卡牌 (无卡号) - 卡名: {card_name[:30]}, 图片: {image_url[:60] if image_url else 'N/A'}")
                    continue
                
                if missing_details:
                    missing_details_count += 1
                
                card = Card(
                    card_no=card_no,
                    card_name=card_name,
                    card_name_ruby=None,
                    card_type=details.get('card_type', ''),
                    color=details.get('color', ''),
                    color2=details.get('color2'),
                    level=details.get('level'),
                    cost=details.get('cost'),
                    dp=details.get('dp'),
                    digivolve_cost1=details.get('digivolve_cost1'),
                    digivolve_cost2=details.get('digivolve_cost2'),
                    digivolve_color1=details.get('digivolve_color1'),
                    digivolve_color2=details.get('digivolve_color2'),
                    form=details.get('form'),
                    attribute=details.get('attribute'),
                    digimon_type=details.get('digimon_type'),
                    effect=details.get('effect'),
                    inherited_effect=details.get('inherited_effect'),
                    security_effect=None,
                    rarity=details.get('rarity', ''),
                    image_url=image_url,
                    parallel_id=None,
                    pack_id=pack.pack_id,
                    pack_name=pack.pack_name,
                    card_url=card_url
                )
                cards.append(card)
                
                if (idx + 1) % 100 == 0:
                    print(f"  已处理 {idx + 1}/{len(card_data_list)} 张卡牌")
            
            if skipped_count > 0:
                print(f"  跳过了 {skipped_count} 张卡牌（无法提取卡号）")
            if missing_details_count > 0:
                print(f"  警告: {missing_details_count} 张卡牌缺少详情（可能是其他卡包的重印卡）")
            print(f"  完成! 共 {len(cards)} 张卡牌")
            
        except Exception as e:
            print(f"获取卡牌失败: {e}")
            import traceback
            traceback.print_exc()
            
        pack.card_count = len(cards)
        return cards
    
    def get_card_details_batch(self, cards: List[Card], batch_size: int = 10) -> List[Card]:
        """批量获取卡牌详情（可选，用于获取完整信息）"""
        print(f"\n开始获取 {len(cards)} 张卡牌的详细信息...")
        
        for idx, card in enumerate(cards):
            if not card.card_url:
                continue
                
            try:
                self.driver.get(card.card_url)
                time.sleep(1)
                
                # 解析详情页
                details = self._parse_detail_page()
                
                # 更新卡牌信息
                if details.get('card_name'):
                    card.card_name = details['card_name']
                if details.get('card_type'):
                    card.card_type = details['card_type']
                if details.get('color'):
                    card.color = details['color']
                if details.get('level'):
                    card.level = details['level']
                if details.get('cost'):
                    card.cost = details['cost']
                if details.get('dp'):
                    card.dp = details['dp']
                if details.get('effect'):
                    card.effect = details['effect']
                if details.get('rarity'):
                    card.rarity = details['rarity']
                    
                if (idx + 1) % 10 == 0:
                    print(f"  详情进度: {idx + 1}/{len(cards)}")
                    
            except Exception as e:
                print(f"  获取详情失败 {card.card_no}: {e}")
                
        return cards

    def _parse_detail_page(self) -> Dict:
        """解析详情页"""
        details = {}
        
        try:
            # 使用JavaScript一次性获取所有信息
            details = self.driver.execute_script("""
                var data = {};
                
                // 卡牌名称
                var nameEl = document.querySelector('.card_name, .cardname, h1.name');
                if (nameEl) data.card_name = nameEl.textContent.trim();
                
                // 卡牌类型
                var typeEl = document.querySelector('.cardtype, [class*="type"]');
                if (typeEl) data.card_type = typeEl.textContent.trim();
                
                // 颜色
                var colorEl = document.querySelector('.color, [class*="color"]');
                if (colorEl) data.color = colorEl.textContent.trim();
                
                // 等级
                var lvEl = document.querySelector('.lv, .level');
                if (lvEl) {
                    var lvMatch = lvEl.textContent.match(/\\d+/);
                    if (lvMatch) data.level = parseInt(lvMatch[0]);
                }
                
                // 费用
                var costEl = document.querySelector('.cost, .play_cost');
                if (costEl) {
                    var costMatch = costEl.textContent.match(/\\d+/);
                    if (costMatch) data.cost = parseInt(costMatch[0]);
                }
                
                // DP
                var dpEl = document.querySelector('.dp');
                if (dpEl) {
                    var dpMatch = dpEl.textContent.match(/\\d+/);
                    if (dpMatch) data.dp = parseInt(dpMatch[0]);
                }
                
                // 效果
                var effectEl = document.querySelector('.effect, .card_effect');
                if (effectEl) data.effect = effectEl.textContent.trim();
                
                // 稀有度
                var rarityEl = document.querySelector('.rarity, [class*="rarity"]');
                if (rarityEl) data.rarity = rarityEl.textContent.trim();
                
                return data;
            """)
        except:
            pass
            
        return details or {}
    
    def debug_card_detail_html(self, category_id: str, card_id: str = "BT24-003"):
        """调试：查看单张卡牌的详情HTML"""
        url = f"{self.CARDLIST_URL}?search=true&category={category_id}"
        print(f"访问: {url}")
        self.driver.get(url)
        time.sleep(5)
        
        result = self.driver.execute_script(f"""
            var detailDiv = document.getElementById('{card_id}');
            
            if (detailDiv) {{
                return {{
                    found: true,
                    html: detailDiv.outerHTML
                }};
            }}
            
            return {{found: false}};
        """)
        
        if result['found']:
            print(f"\n=== 卡牌 {card_id} 详情HTML ===")
            print(result['html'])
            
            # 保存到文件
            with open(f"output/card_{card_id}_detail.html", "w", encoding="utf-8") as f:
                f.write(result['html'])
            print(f"\nHTML已保存到: output/card_{card_id}_detail.html")
        else:
            print(f"未找到卡牌 {card_id} 的详情")
    
    def debug_detail_elements(self, category_id: str):
        """调试：检查详情元素"""
        url = f"{self.CARDLIST_URL}?search=true&category={category_id}"
        print(f"访问: {url}")
        self.driver.get(url)
        time.sleep(5)
        
        result = self.driver.execute_script("""
            var result = {
                hasDetailDiv: false,
                detailIds: [],
                sampleDetailHtml: '',
                allDivIds: []
            };
            
            // 查找第一个卡牌的 data-src
            var firstLink = document.querySelector('a[data-src]');
            if (firstLink) {
                var dataSrc = firstLink.getAttribute('data-src');
                result.firstDataSrc = dataSrc;
                
                if (dataSrc) {
                    var detailId = dataSrc.replace('#', '');
                    var detailDiv = document.getElementById(detailId);
                    
                    if (detailDiv) {
                        result.hasDetailDiv = true;
                        result.sampleDetailHtml = detailDiv.outerHTML.substring(0, 2000);
                    } else {
                        result.hasDetailDiv = false;
                        result.message = 'Detail div not found for ID: ' + detailId;
                    }
                }
            }
            
            // 查找所有带ID的div
            var allDivs = document.querySelectorAll('div[id]');
            allDivs.forEach(function(div) {
                var id = div.id;
                if (id.match(/[A-Z]{2,3}\d{2}-\d{3}/)) {
                    result.detailIds.push(id);
                }
                if (result.allDivIds.length < 20) {
                    result.allDivIds.push(id);
                }
            });
            
            return result;
        """)
        
        print("\n=== 详情元素检查 ===")
        print(f"第一个卡牌的 data-src: {result.get('firstDataSrc', 'N/A')}")
        print(f"是否找到详情div: {result.get('hasDetailDiv', False)}")
        print(f"找到的卡牌详情ID数量: {len(result.get('detailIds', []))}")
        print(f"前20个div ID: {result.get('allDivIds', [])}")
        
        if result.get('sampleDetailHtml'):
            print(f"\n示例详情HTML:\n{result['sampleDetailHtml']}")
        else:
            print(f"\n消息: {result.get('message', 'No detail found')}")
    
    def get_all_packs(self) -> List[CardPack]:
        """获取所有卡包列表"""
        packs = []
        
        try:
            print("\n正在获取卡包列表...")
            self.driver.get(f"{self.CARDLIST_URL}?search=true")
            time.sleep(3)
            
            # 使用JavaScript获取所有卡包选项
            pack_data = self.driver.execute_script("""
                var packs = [];
                var select = document.querySelector('select[name="category"]');
                
                if (select) {
                    var options = select.querySelectorAll('option');
                    options.forEach(function(option) {
                        var value = option.value;
                        var text = option.textContent.trim();
                        if (value && value !== '' && text && text !== '') {
                            packs.push({
                                id: value,
                                name: text
                            });
                        }
                    });
                }
                
                return packs;
            """)
            
            for data in pack_data:
                pack_id = data['id']
                pack_name = data['name']
                pack_code = self._extract_pack_code(pack_name)
                
                pack = CardPack(
                    pack_id=pack_id,
                    pack_name=pack_name,
                    pack_code=pack_code,
                    release_date=None,
                    pack_url=f"{self.CARDLIST_URL}?search=true&category={pack_id}"
                )
                packs.append(pack)
                
            print(f"找到 {len(packs)} 个卡包")
            
        except Exception as e:
            print(f"获取卡包列表失败: {e}")
            import traceback
            traceback.print_exc()
            
        return packs
    
    def _extract_pack_code(self, pack_name: str) -> str:
        """从卡包名称中提取卡包代码"""
        match = re.search(r'[A-Z]{2,3}-?\d{1,2}', pack_name)
        return match.group() if match else ""
    
    def scrape_single_pack(self, category_id: str, get_details: bool = False) -> tuple:
        """爬取单个卡包"""
        pack = CardPack(
            pack_id=category_id,
            pack_name="",
            pack_code="",
            release_date=None,
            pack_url=f"{self.CARDLIST_URL}?search=true&category={category_id}"
        )
        
        self.driver.get(pack.pack_url)
        time.sleep(3)
        
        # 获取卡包名称
        try:
            title = self.driver.execute_script("return document.title || '';")
            pack.pack_name = title.split('｜')[0].strip() if '｜' in title else title
            pack.pack_code = self._extract_pack_code(pack.pack_name)
        except:
            pass
        
        cards = self.get_cards_from_pack(pack)
        
        if get_details and cards:
            cards = self.get_card_details_batch(cards)
        
        return pack, cards
    
    def scrape_all(self, max_packs: int = None, get_details: bool = False) -> tuple:
        """爬取所有卡包和卡牌"""
        all_packs = []
        all_cards = []
        
        packs = self.get_all_packs()
        
        if max_packs:
            packs = packs[:max_packs]
            print(f"\n限制爬取前 {max_packs} 个卡包")
        
        print(f"\n开始爬取 {len(packs)} 个卡包...\n")
        
        for idx, pack in enumerate(packs):
            print(f"\n[{idx+1}/{len(packs)}] 处理卡包: {pack.pack_name}")
            
            try:
                cards = self.get_cards_from_pack(pack)
                
                if get_details and cards:
                    cards = self.get_card_details_batch(cards)
                
                # 立即保存当前卡包
                self.save_pack_to_json(pack, cards)
                
                all_packs.append(pack)
                all_cards.extend(cards)
                
                # 礼貌性延迟
                time.sleep(2)
                
            except Exception as e:
                print(f"  爬取失败: {e}")
                import traceback
                traceback.print_exc()
                all_packs.append(pack)
        
        # 最后保存汇总文件
        print(f"\n\n=== 爬取完成，保存汇总文件 ===")
        return all_packs, all_cards
    
    def save_pack_to_json(self, pack: CardPack, cards: List[Card]):
        """保存单个卡包数据到JSON文件"""
        # 清理文件名，移除特殊字符
        safe_name = pack.pack_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = safe_name.replace(':', '_').replace('*', '_').replace('?', '_')
        safe_name = safe_name.replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        
        # 构建文件名
        filename = f"digimon_cards_{safe_name}"
        
        # 保存卡包信息
        pack_file = os.path.join(self.output_dir, f"{filename}_pack.json")
        with open(pack_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(pack), f, ensure_ascii=False, indent=2)
        
        # 保存卡牌数据
        cards_file = os.path.join(self.output_dir, f"{filename}_cards.json")
        with open(cards_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(c) for c in cards], f, ensure_ascii=False, indent=2)
        
        print(f"  已保存: {cards_file} ({len(cards)} 张卡牌)")
        
        return pack_file, cards_file
    
    def save_to_json(self, packs: List[CardPack], cards: List[Card], filename: str = None):
        """保存数据到JSON（汇总文件）"""
        if filename is None:
            filename = f"digimon_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 保存卡包
        packs_file = os.path.join(self.output_dir, f"{filename}_packs.json")
        with open(packs_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in packs], f, ensure_ascii=False, indent=2)
        print(f"\n卡包数据: {packs_file}")
        
        # 保存卡牌
        cards_file = os.path.join(self.output_dir, f"{filename}_cards.json")
        with open(cards_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(c) for c in cards], f, ensure_ascii=False, indent=2)
        print(f"卡牌数据: {cards_file}")
        
        print(f"\n总计: {len(packs)} 个卡包, {len(cards)} 张卡牌")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="数码宝贝卡牌爬虫 v2")
    parser.add_argument("--category", type=str, help="卡包category ID（指定则只爬取该卡包）")
    parser.add_argument("--all", action="store_true", help="爬取所有卡包")
    parser.add_argument("--debug", action="store_true", help="调试模式：检查详情元素")
    parser.add_argument("--max-packs", type=int, help="最大爬取卡包数量（用于测试）")
    parser.add_argument("--output", type=str, default="output", help="输出目录")
    parser.add_argument("--details", action="store_true", help="获取详细信息（较慢）")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器")
    parser.add_argument("--driver-path", type=str, help="ChromeDriver路径")
    
    args = parser.parse_args()
    
    # 检查参数
    if not args.category and not args.all and not args.debug:
        parser.error("请指定 --category <ID>、--all 或 --debug")
    
    with DigimonCardScraper(
        headless=not args.no_headless, 
        output_dir=args.output,
        chrome_driver_path=args.driver_path
    ) as scraper:
        if args.debug:
            # 调试模式
            category = args.category or "503035"
            if args.category and len(args.category.split('-')) == 2:
                # 如果提供的是卡号格式，查看该卡的详情HTML
                scraper.debug_card_detail_html("503035", args.category)
            else:
                scraper.debug_detail_elements(category)
        elif args.category:
            # 爬取单个卡包
            pack, cards = scraper.scrape_single_pack(args.category, get_details=args.details)
            scraper.save_pack_to_json(pack, cards)
            print(f"\n总计: 1 个卡包, {len(cards)} 张卡牌")
        else:
            # 爬取所有卡包
            packs, cards = scraper.scrape_all(max_packs=args.max_packs, get_details=args.details)
            scraper.save_to_json(packs, cards)
    
    print("\n完成!")


if __name__ == "__main__":
    main()
