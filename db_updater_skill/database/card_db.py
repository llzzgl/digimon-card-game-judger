"""
卡牌数据库管理
"""

import json
import os
from pathlib import Path
from datetime import datetime


class CardDatabase:
    """卡牌数据库管理类"""
    
    def __init__(self):
        self.cards = []
        self.card_index = {}  # card_no -> card
        
    def load_from_folder(self, folder_path):
        """
        从文件夹加载卡牌数据
        
        Args:
            folder_path: 包含卡牌 JSON 文件的文件夹路径
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            print(f"⚠ 文件夹不存在：{folder_path}")
            return
        
        print(f"\n从 {folder_path} 加载卡牌数据...")
        
        # 查找所有卡牌 JSON 文件
        json_files = list(folder_path.glob("*_cards.json"))
        
        total_cards = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    if isinstance(cards, list):
                        self.cards.extend(cards)
                        total_cards += len(cards)
                        print(f"  ✓ {json_file.name}: {len(cards)} 张卡牌")
            except Exception as e:
                print(f"  ✗ {json_file.name} 加载失败：{e}")
        
        print(f"✓ 共加载 {total_cards} 张卡牌")
        
        # 构建索引
        self._build_index()
    
    def _build_index(self):
        """构建卡牌索引"""
        self.card_index = {}
        for card in self.cards:
            card_no = card.get('card_no')
            if card_no:
                self.card_index[card_no] = card
    
    def merge_and_deduplicate(self):
        """合并并去重"""
        print("\n合并并去重卡牌数据...")
        
        # 使用索引去重（后加载的覆盖先加载的）
        unique_cards = {}
        for card in self.cards:
            card_no = card.get('card_no')
            if card_no:
                unique_cards[card_no] = card
        
        self.cards = list(unique_cards.values())
        self._build_index()
        
        print(f"✓ 去重后剩余 {len(self.cards)} 张卡牌")
    
    def save_to_json(self, output_path):
        """
        保存为 JSON 文件
        
        Args:
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n保存到 {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.cards, f, ensure_ascii=False, indent=2)
        
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ 保存完成 ({file_size:.2f} MB)")
    
    def search_by_card_no(self, card_no):
        """根据卡牌编号搜索"""
        return self.card_index.get(card_no)
    
    def search_by_name(self, name):
        """根据卡牌名称搜索（模糊匹配）"""
        results = []
        for card in self.cards:
            card_name = card.get('card_name', '')
            if name.lower() in card_name.lower():
                results.append(card)
        return results
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            "total_cards": len(self.cards),
            "unique_card_nos": len(self.card_index),
            "by_type": {},
            "by_color": {},
        }
        
        for card in self.cards:
            # 按类型统计
            card_type = card.get('card_type', 'Unknown')
            stats["by_type"][card_type] = stats["by_type"].get(card_type, 0) + 1
            
            # 按颜色统计
            color = card.get('color', 'Unknown')
            if color:
                stats["by_color"][color] = stats["by_color"].get(color, 0) + 1
        
        return stats


if __name__ == "__main__":
    # 测试
    db = CardDatabase()
    db.load_from_folder("../../digimon_card_data")
    db.merge_and_deduplicate()
    db.save_to_json("../../skill/data/cards.json")
    
    print("\n统计信息:")
    stats = db.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
