"""
DTCG 多语言卡牌关联系统
实现日/中/英卡牌关联，支持多语言查询
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class MultilingualCardLinker:
    """多语言卡牌关联器"""
    
    def __init__(self, db_path: str = "card_data/card_metadata.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """创建多语言关联表"""
        cursor = self.conn.cursor()
        
        # 多语言关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_translations (
                translation_id TEXT PRIMARY KEY,
                base_card_id TEXT,
                language TEXT,
                card_name TEXT,
                card_name_ruby TEXT,
                effect TEXT,
                inherited_effect TEXT,
                security_effect TEXT,
                image_url TEXT,
                FOREIGN KEY (base_card_id) REFERENCES cards(card_id)
            )
        """)
        
        # 卡牌变体表（异画、不同语言版本）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_variants (
                variant_id TEXT PRIMARY KEY,
                base_card_id TEXT,
                variant_type TEXT,
                language TEXT,
                card_id TEXT,
                pack TEXT,
                image_path TEXT,
                FOREIGN KEY (base_card_id) REFERENCES cards(card_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_translations_base ON card_translations(base_card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_translations_lang ON card_translations(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_variants_base ON card_variants(base_card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_variants_lang ON card_variants(language)")
        
        self.conn.commit()
    
    def link_cards(self, jp_card_id: str, cn_card_id: str = None, en_card_id: str = None) -> str:
        """
        关联不同语言的同一张卡牌
        
        Args:
            jp_card_id: 日文卡牌 ID (如 BT1-001)
            cn_card_id: 中文卡牌 ID (如 AD1-001)
            en_card_id: 英文卡牌 ID
        
        Returns:
            base_card_id: 基础卡牌 ID
        """
        cursor = self.conn.cursor()
        
        # 使用日文卡牌 ID 作为基础 ID
        base_card_id = jp_card_id
        
        # 检查是否已有关联
        cursor.execute("SELECT base_card_id FROM card_variants WHERE card_id = ?", (jp_card_id,))
        row = cursor.fetchone()
        if row:
            base_card_id = row[0]
        
        # 关联日文卡牌
        cursor.execute("""
            INSERT OR REPLACE INTO card_variants
            (variant_id, base_card_id, variant_type, language, card_id)
            VALUES (?, ?, ?, ?, ?)
        """, (f"{base_card_id}_jp", base_card_id, "original", "ja", jp_card_id))
        
        # 关联中文卡牌
        if cn_card_id:
            cursor.execute("""
                INSERT OR REPLACE INTO card_variants
                (variant_id, base_card_id, variant_type, language, card_id)
                VALUES (?, ?, ?, ?, ?)
            """, (f"{base_card_id}_cn", base_card_id, "translation", "zh", cn_card_id))
        
        # 关联英文卡牌
        if en_card_id:
            cursor.execute("""
                INSERT OR REPLACE INTO card_variants
                (variant_id, base_card_id, variant_type, language, card_id)
                VALUES (?, ?, ?, ?, ?)
            """, (f"{base_card_id}_en", base_card_id, "translation", "en", en_card_id))
        
        self.conn.commit()
        return base_card_id
    
    def get_multilingual_card(self, card_id: str) -> Dict:
        """
        获取卡牌的多语言信息
        
        Args:
            card_id: 任意语言的卡牌 ID
        
        Returns:
            包含所有语言信息的字典
        """
        cursor = self.conn.cursor()
        
        # 查找基础卡牌 ID
        cursor.execute("SELECT base_card_id FROM card_variants WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        
        if not row:
            # 没有关联，直接返回原卡牌信息
            return self._get_card_info(card_id)
        
        base_card_id = row[0]
        
        # 获取所有变体
        cursor.execute("""
            SELECT variant_id, variant_type, language, card_id, pack, image_path
            FROM card_variants
            WHERE base_card_id = ?
        """, (base_card_id,))
        
        variants = []
        for row in cursor.fetchall():
            variant = {
                'variant_id': row[0],
                'variant_type': row[1],
                'language': row[2],
                'card_id': row[3],
                'pack': row[4],
                'image_path': row[5],
                'card_info': self._get_card_info(row[3])
            }
            variants.append(variant)
        
        # 获取翻译
        cursor.execute("""
            SELECT language, card_name, effect, inherited_effect, security_effect
            FROM card_translations
            WHERE base_card_id = ?
        """, (base_card_id,))
        
        translations = {}
        for row in cursor.fetchall():
            translations[row[0]] = {
                'card_name': row[1],
                'effect': row[2],
                'inherited_effect': row[3],
                'security_effect': row[4]
            }
        
        return {
            'base_card_id': base_card_id,
            'variants': variants,
            'translations': translations,
            'primary': self._get_card_info(base_card_id)
        }
    
    def _get_card_info(self, card_id: str) -> Optional[Dict]:
        """获取卡牌信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def search_multilingual(self, query: str, language: str = "zh", limit: int = 10) -> List[Dict]:
        """
        多语言搜索
        
        Args:
            query: 搜索词
            language: 优先语言 (zh/ja/en)
            limit: 返回数量
        
        Returns:
            卡牌列表（优先显示指定语言）
        """
        cursor = self.conn.cursor()
        
        # 搜索所有语言
        cursor.execute("""
            SELECT DISTINCT c.* FROM cards c
            LEFT JOIN card_variants cv ON c.card_id = cv.card_id
            WHERE c.card_id LIKE ? OR c.card_name LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit * 2))
        
        results = []
        for row in cursor.fetchall():
            card = dict(zip([d[0] for d in cursor.description], row))
            
            # 获取多语言信息
            multi_info = self.get_multilingual_card(card['card_id'])
            
            # 优先返回指定语言的信息
            if language in multi_info.get('translations', {}):
                trans = multi_info['translations'][language]
                card['display_name'] = trans.get('card_name', card.get('card_name'))
                card['display_effect'] = trans.get('effect', card.get('effect'))
            else:
                card['display_name'] = card.get('card_name')
                card['display_effect'] = card.get('effect')
            
            card['multi_info'] = multi_info
            results.append(card)
        
        return results[:limit]
    
    def close(self):
        self.conn.close()


def main():
    """主函数 - 自动关联中日文卡牌"""
    print("=" * 60)
    print("DTCG 多语言卡牌关联系统")
    print("=" * 60)
    print()
    
    linker = MultilingualCardLinker()
    
    # 示例：关联 AD-01 系列
    print("关联 AD-01 系列卡牌...")
    
    # 这里需要根据实际的卡牌编号进行关联
    # 示例关联
    linker.link_cards("AD1-001", "AD1-001")
    linker.link_cards("AD1-025", "AD1-025")
    
    # 测试搜索
    print("\n测试多语言搜索 (zh)...")
    results = linker.search_multilingual("奥米加", language="zh", limit=5)
    
    for card in results:
        print(f"  {card.get('card_id')} - {card.get('display_name', 'N/A')}")
    
    linker.close()
    print("\n关联系统就绪！")


if __name__ == "__main__":
    main()
