"""
DTCG 卡牌元数据关联系统
基于现有卡牌数据构建图片 - 卡牌关联索引
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib

# Windows 控制台编码修复
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


@dataclass
class CardMetadata:
    """卡牌元数据"""
    card_id: str
    card_name: str
    pack: str
    rarity: str
    card_type: str = ""
    color: str = ""
    level: str = ""
    cost: str = ""
    dp: str = ""
    attribute: str = ""
    digimon_type: str = ""
    effect: str = ""
    image_url: str = ""
    image_path: str = ""
    alt_art: bool = False
    alt_type: str = ""


class CardMetadataDB:
    """卡牌元数据数据库"""
    
    def __init__(self, db_path: str = "card_data/card_metadata.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 卡牌主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                card_name TEXT,
                pack TEXT,
                rarity TEXT,
                card_type TEXT,
                color TEXT,
                level TEXT,
                cost TEXT,
                dp TEXT,
                attribute TEXT,
                digimon_type TEXT,
                effect TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 图片索引表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                image_id TEXT PRIMARY KEY,
                card_id TEXT,
                image_type TEXT,
                image_path TEXT,
                image_hash TEXT,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        """)
        
        # 异画版本表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alt_arts (
                alt_id TEXT PRIMARY KEY,
                base_card_id TEXT,
                alt_type TEXT,
                image_path TEXT,
                FOREIGN KEY (base_card_id) REFERENCES cards(card_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_card ON images(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alt_arts_base ON alt_arts(base_card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_pack ON cards(pack)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_rarity ON cards(rarity)")
        
        self.conn.commit()
    
    def insert_card(self, card: CardMetadata):
        """插入卡牌数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cards 
            (card_id, card_name, pack, rarity, card_type, color, level, cost, dp, attribute, digimon_type, effect, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.card_id, card.card_name, card.pack, card.rarity,
            card.card_type, card.color, card.level, card.cost, card.dp,
            card.attribute, card.digimon_type, card.effect, card.image_url
        ))
        self.conn.commit()
    
    def insert_image(self, image_id: str, card_id: str, image_type: str, 
                     image_path: str, image_hash: str = "", 
                     width: int = 0, height: int = 0, file_size: int = 0):
        """插入图片索引"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO images
            (image_id, card_id, image_type, image_path, image_hash, width, height, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (image_id, card_id, image_type, image_path, image_hash, width, height, file_size))
        self.conn.commit()
    
    def insert_alt_art(self, alt_id: str, base_card_id: str, alt_type: str, image_path: str):
        """插入异画版本"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO alt_arts
            (alt_id, base_card_id, alt_type, image_path)
            VALUES (?, ?, ?, ?)
        """, (alt_id, base_card_id, alt_type, image_path))
        self.conn.commit()
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """根据卡牌 ID 查询"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def get_card_by_image(self, image_path: str) -> Optional[Dict]:
        """根据图片路径查询卡牌"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.* FROM cards c
            JOIN images i ON c.card_id = i.card_id
            WHERE i.image_path = ?
        """, (image_path,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def get_images_for_card(self, card_id: str) -> List[Dict]:
        """获取卡牌的所有图片"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE card_id = ?", (card_id,))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    
    def search_cards(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索卡牌"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM cards 
            WHERE card_id LIKE ? OR card_name LIKE ? OR pack LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images")
        image_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alt_arts")
        alt_count = cursor.fetchone()[0]
        return {
            "total_cards": card_count,
            "total_images": image_count,
            "total_alt_arts": alt_count
        }
    
    def close(self):
        """关闭数据库"""
        self.conn.close()


def build_metadata_from_existing_data(project_root: Path):
    """从现有数据构建元数据"""
    print("从现有数据构建元数据关联系统...")
    
    # 初始化数据库
    db = CardMetadataDB(str(project_root / "card_data" / "card_metadata.db"))
    
    # 读取现有卡牌数据 - 支持多个 JSON 文件
    cards_dir = project_root / "digimon_card_data"
    all_cards_data = []
    
    if cards_dir.exists():
        for cards_file in cards_dir.glob("*.json"):
            print(f"读取卡牌数据：{cards_file}")
            try:
                with open(cards_file, 'r', encoding='utf-8') as f:
                    cards_data = json.load(f)
                print(f"  - 加载了 {len(cards_data)} 张卡牌数据")
                all_cards_data.extend(cards_data)
            except Exception as e:
                print(f"  - 读取失败：{e}")
        
        if all_cards_data:
            # 去重 - 只处理字典类型的数据
            seen_ids = set()
            unique_cards = []
            for card_data in all_cards_data:
                # 跳过非字典类型（如字符串）
                if not isinstance(card_data, dict):
                    continue
                card_id = card_data.get('card_no', '')
                if card_id and card_id not in seen_ids:
                    seen_ids.add(card_id)
                    unique_cards.append(card_data)
            
            all_cards_data = unique_cards
            print(f"总计 {len(all_cards_data)} 张唯一卡牌数据")
            
            # 插入数据库
            for card_data in all_cards_data:
                card = CardMetadata(
                    card_id=card_data.get('card_no', ''),
                    card_name=card_data.get('card_name', ''),
                    pack=card_data.get('pack_name', ''),
                    rarity=card_data.get('rarity', ''),
                    card_type=card_data.get('card_type', ''),
                    color=card_data.get('color', ''),
                    level=str(card_data.get('level', '')),
                    cost=str(card_data.get('cost', '')),
                    dp=str(card_data.get('dp', '')),
                    attribute=card_data.get('attribute', ''),
                    digimon_type=card_data.get('digimon_type', ''),
                    effect=card_data.get('effect', ''),
                    image_url=card_data.get('image_url', '')
                )
                db.insert_card(card)
            
            print(f"已插入 {len(all_cards_data)} 张卡牌到数据库")
    
    # 扫描现有图片并建立关联
    images_dir = project_root / "card_data" / "images" / "cn" / "raw"
    if images_dir.exists():
        print(f"扫描图片目录：{images_dir}")
        image_files = list(images_dir.glob("*.jpg"))
        print(f"找到 {len(image_files)} 张图片")
        
        for img_path in image_files:
            # 从文件名提取卡牌 ID
            filename = img_path.name
            # 例：AD-01_AD1-001_12571_19729_MxZmL89JbH3_jpg~card.jpg
            # 或：EX-11CN_EX11-001_12202_19354_MAVKtf6Dcx6_png~card.jpg
            
            parts = filename.split('_')
            if len(parts) >= 2:
                # 提取卡牌编号
                card_no = parts[1] if len(parts) > 1 else parts[0]
                
                # 计算图片哈希
                with open(img_path, 'rb') as f:
                    img_hash = hashlib.md5(f.read()).hexdigest()
                
                # 获取文件大小
                file_size = img_path.stat().st_size
                
                # 插入图片索引
                image_id = img_path.stem
                db.insert_image(
                    image_id=image_id,
                    card_id=card_no,
                    image_type="normal",
                    image_path=str(img_path.relative_to(project_root)),
                    image_hash=img_hash,
                    file_size=file_size
                )
        
        print(f"已建立 {len(image_files)} 张图片的索引")
    
    # 输出统计
    stats = db.get_stats()
    print("\n=== 元数据系统统计 ===")
    print(f"卡牌总数：{stats['total_cards']}")
    print(f"图片总数：{stats['total_images']}")
    print(f"异画版本：{stats['total_alt_arts']}")
    
    db.close()
    print("\n元数据系统构建完成！")
    
    return stats


if __name__ == "__main__":
    project_root = Path(__file__).parent
    build_metadata_from_existing_data(project_root)
