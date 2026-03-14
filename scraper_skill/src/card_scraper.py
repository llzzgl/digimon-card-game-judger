"""
卡牌爬虫统一接口
整合日文和中文卡牌爬虫功能
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .utils.jp_scraper import JapaneseCardScraper
from .utils.cn_scraper import ChineseCardScraper

logger = logging.getLogger(__name__)


class CardScraper:
    """
    卡牌爬虫统一接口
    提供日文和中文卡牌爬取功能
    """
    
    def __init__(self, config: dict = None):
        """
        初始化卡牌爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.output_path = Path(self.config.get("output_path", "cards.json"))
        
        # 初始化子爬虫
        self.jp_scraper = JapaneseCardScraper(self.config.get("jp", {}))
        self.cn_scraper = ChineseCardScraper(self.config.get("cn", {}))
        
        # 合并后的卡牌数据
        self.cards = {}  # card_no -> card_data
    
    def scrape_japanese(self, category_ids: List[str] = None, output_path: Path = None) -> List[Dict]:
        """
        爬取日文卡牌
        
        Args:
            category_ids: 卡包 ID 列表
            output_path: 输出路径
            
        Returns:
            卡牌列表
        """
        logger.info("\n" + "="*60)
        logger.info("开始爬取日文卡牌")
        logger.info("="*60)
        
        try:
            cards = self.jp_scraper.scrape_all(category_ids)
            
            # 保存到指定路径
            if output_path:
                self.jp_scraper.save_to_json(cards, output_path)
            
            # 合并到总数据
            for card in cards:
                from dataclasses import asdict
                card_data = asdict(card) if hasattr(card, '__dataclass_fields__') else card
                if card_data.get('card_no'):
                    self.cards[card_data['card_no']] = card_data
            
            logger.info(f"✓ 日文卡牌爬取完成，共 {len(cards)} 张")
            return cards
            
        except Exception as e:
            logger.error(f"日文卡牌爬取失败：{e}")
            return []
        finally:
            self.jp_scraper.close()
    
    def scrape_chinese(self, max_pages: int = None, output_path: Path = None) -> int:
        """
        爬取中文卡牌
        
        Args:
            max_pages: 最大页数
            output_path: 输出路径
            
        Returns:
            新增卡牌数量
        """
        logger.info("\n" + "="*60)
        logger.info("开始爬取中文卡牌")
        logger.info("="*60)
        
        try:
            if output_path:
                self.cn_scraper.output_path = output_path
            
            new_count = self.cn_scraper.scrape_all_cards(max_pages)
            
            # 加载到总数据
            self.cn_scraper.load_existing_data()
            for card in self.cn_scraper.get_all_cards():
                if card.get('card_no'):
                    self.cards[card['card_no']] = card
            
            logger.info(f"✓ 中文卡牌爬取完成，新增 {new_count} 张")
            return new_count
            
        except Exception as e:
            logger.error(f"中文卡牌爬取失败：{e}")
            return 0
        finally:
            self.cn_scraper.close()
    
    def merge_cards(self, jp_path: Path = None, cn_path: Path = None) -> Dict[str, Dict]:
        """
        合并日文和中文卡牌数据
        
        Args:
            jp_path: 日文卡牌 JSON 路径
            cn_path: 中文卡牌 JSON 路径
            
        Returns:
            合并后的卡牌字典
        """
        logger.info("开始合并卡牌数据")
        
        # 加载日文卡牌
        if jp_path and jp_path.exists():
            with open(jp_path, 'r', encoding='utf-8') as f:
                jp_cards = json.load(f)
                for card in jp_cards:
                    if card.get('card_no'):
                        self.cards[card['card_no']] = card
                logger.info(f"✓ 加载 {len(jp_cards)} 张日文卡牌")
        
        # 加载中文卡牌
        if cn_path and cn_path.exists():
            with open(cn_path, 'r', encoding='utf-8') as f:
                cn_cards = json.load(f)
                for card in cn_cards:
                    if card.get('card_no'):
                        # 如果已有日文数据，合并；否则直接添加
                        card_no = card['card_no']
                        if card_no in self.cards:
                            # 合并中文信息
                            self.cards[card_no].update({
                                'name_cn': card.get('name_cn', ''),
                                'type_cn': card.get('type', ''),
                                'effect_cn': card.get('effect', ''),
                            })
                        else:
                            self.cards[card_no] = card
                logger.info(f"✓ 加载 {len(cn_cards)} 张中文卡牌")
        
        logger.info(f"✓ 合并完成，共 {len(self.cards)} 张卡牌")
        return self.cards
    
    def save_merged(self, output_path: Path = None):
        """
        保存合并后的卡牌数据
        
        Args:
            output_path: 输出路径
        """
        if output_path is None:
            output_path = self.output_path
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data_list = list(self.cards.values())
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ 合并数据已保存到：{output_path}")
    
    def validate_cards(self, cards: List[Dict] = None) -> Dict:
        """
        验证卡牌数据
        
        Args:
            cards: 卡牌列表（可选，默认使用 self.cards）
            
        Returns:
            验证报告
        """
        if cards is None:
            cards = list(self.cards.values())
        
        required_fields = ['card_no', 'card_name', 'card_type']
        optional_fields = ['color', 'level', 'cost', 'dp', 'effect', 'rarity']
        
        report = {
            'total': len(cards),
            'valid': 0,
            'invalid': 0,
            'missing_fields': {},
            'errors': []
        }
        
        for card in cards:
            is_valid = True
            
            # 检查必填字段
            for field in required_fields:
                if not card.get(field):
                    is_valid = False
                    if field not in report['missing_fields']:
                        report['missing_fields'][field] = 0
                    report['missing_fields'][field] += 1
            
            if is_valid:
                report['valid'] += 1
            else:
                report['invalid'] += 1
                report['errors'].append({
                    'card_no': card.get('card_no', 'UNKNOWN'),
                    'missing': [f for f in required_fields if not card.get(f)]
                })
        
        logger.info(f"验证完成：{report['valid']} 有效 / {report['invalid']} 无效")
        return report
    
    def get_card(self, card_no: str) -> Optional[Dict]:
        """
        获取单张卡牌
        
        Args:
            card_no: 卡牌编号
            
        Returns:
            卡牌数据或 None
        """
        return self.cards.get(card_no)
    
    def search_by_name(self, name: str, lang: str = 'jp') -> List[Dict]:
        """
        根据名称搜索卡牌
        
        Args:
            name: 卡牌名称
            lang: 语言（'jp' 或 'cn'）
            
        Returns:
            匹配的卡牌列表
        """
        results = []
        name_lower = name.lower()
        
        for card in self.cards.values():
            if lang == 'jp':
                card_name = card.get('card_name', '').lower()
            else:
                card_name = card.get('name_cn', '').lower()
            
            if name_lower in card_name:
                results.append(card)
        
        return results
