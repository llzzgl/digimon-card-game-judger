"""
DTCG 卡牌多模态识别系统 v1
支持：图片→卡牌信息识别
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
from PIL import Image
import numpy as np


class CardRecognizer:
    """卡牌识别器 - 基于特征匹配"""
    
    def __init__(self, db_path: str = "card_data/card_metadata.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.image_features = {}  # 缓存图片特征
        self._load_image_index()
    
    def _load_image_index(self):
        """加载图片索引"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT image_id, card_id, image_path, image_hash FROM images")
        for row in cursor.fetchall():
            image_id, card_id, image_path, image_hash = row
            self.image_features[image_id] = {
                'card_id': card_id,
                'image_path': image_path,
                'image_hash': image_hash
            }
        print(f"已加载 {len(self.image_features)} 张图片索引")
    
    def _extract_features(self, image_path: Path) -> Dict:
        """提取图片特征（简化版：使用哈希 + 尺寸）"""
        if not image_path.exists():
            return {}
        
        try:
            # 计算感知哈希（简化版）
            with Image.open(image_path) as img:
                # 调整到固定尺寸
                img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)
                # 转换为灰度
                img_gray = img_resized.convert('L')
                # 计算平均亮度
                pixels = list(img_gray.getdata())
                avg_brightness = sum(pixels) / len(pixels)
                # 生成简单特征
                feature = {
                    'width': img.width,
                    'height': img.height,
                    'avg_brightness': avg_brightness,
                    'hash': hashlib.md5(img_gray.tobytes()).hexdigest()[:16]
                }
            return feature
        except Exception as e:
            print(f"提取特征失败：{e}")
            return {}
    
    def _compute_similarity(self, feat1: Dict, feat2: Dict) -> float:
        """计算特征相似度"""
        if not feat1 or not feat2:
            return 0.0
        
        score = 0.0
        factors = 0
        
        # 尺寸匹配
        if feat1.get('width') == feat2.get('width'):
            score += 0.3
        factors += 0.3
        
        if feat1.get('height') == feat2.get('height'):
            score += 0.3
        factors += 0.3
        
        # 哈希匹配（简化）
        if feat1.get('hash', '')[:8] == feat2.get('hash', '')[:8]:
            score += 0.4
        factors += 0.4
        
        return score / factors if factors > 0 else 0.0
    
    def recognize(self, image_path: str, top_k: int = 3) -> List[Dict]:
        """
        识别卡牌图片
        
        Args:
            image_path: 输入图片路径
            top_k: 返回最匹配的 K 个结果
        
        Returns:
            匹配的卡牌列表（按相似度排序）
        """
        image_path = Path(image_path)
        if not image_path.exists():
            return []
        
        # 提取输入图片特征
        input_features = self._extract_features(image_path)
        input_hash = hashlib.md5(image_path.read_bytes()).hexdigest()
        
        print(f"识别图片：{image_path.name}")
        print(f"  特征：{input_features}")
        
        results = []
        
        # 精确匹配（哈希完全相同）
        for image_id, info in self.image_features.items():
            if info['image_hash'] == input_hash:
                # 找到完全匹配
                card_info = self._get_card_info(info['card_id'])
                if card_info:
                    results.append({
                        'card': card_info,
                        'similarity': 1.0,
                        'match_type': 'exact',
                        'image_path': info['image_path']
                    })
        
        # 如果没有精确匹配，使用特征相似度
        if not results:
            print("  未找到精确匹配，使用特征相似度...")
            similarities = []
            
            for image_id, info in self.image_features.items():
                # 加载缓存特征或重新计算
                ref_image_path = Path(image_path.parent.parent / "cn" / "raw" / Path(info['image_path']).name)
                if ref_image_path.exists():
                    ref_features = self._extract_features(ref_image_path)
                    sim = self._compute_similarity(input_features, ref_features)
                    
                    if sim > 0.5:  # 阈值
                        card_info = self._get_card_info(info['card_id'])
                        if card_info:
                            similarities.append({
                                'card': card_info,
                                'similarity': sim,
                                'match_type': 'fuzzy',
                                'image_path': info['image_path']
                            })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:top_k]
        
        return results
    
    def _get_card_info(self, card_id: str) -> Optional[Dict]:
        """获取卡牌信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def search_by_text(self, query: str, limit: int = 5) -> List[Dict]:
        """文本搜索卡牌"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM cards 
            WHERE card_id LIKE ? OR card_name LIKE ? 
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    
    def close(self):
        """关闭数据库"""
        self.conn.close()


def test_recognition(project_root: Path):
    """测试识别功能"""
    print("=" * 60)
    print("DTCG 卡牌识别系统测试")
    print("=" * 60)
    
    recognizer = CardRecognizer(str(project_root / "card_data" / "card_metadata.db"))
    
    # 测试图片目录
    test_images_dir = project_root / "card_data" / "images" / "cn" / "raw"
    
    if test_images_dir.exists():
        test_images = list(test_images_dir.glob("*.jpg"))[:5]
        
        for img_path in test_images:
            print(f"\n测试图片：{img_path.name}")
            results = recognizer.recognize(str(img_path))
            
            if results:
                print(f"  识别结果：{len(results)} 个匹配")
                for i, result in enumerate(results[:3], 1):
                    card = result['card']
                    print(f"  {i}. {card['card_id']} - {card['card_name']}")
                    print(f"     相似度：{result['similarity']:.2f} ({result['match_type']})")
                    print(f"     卡包：{card['pack']} | 稀有度：{card['rarity']}")
            else:
                print(f"  [X] 未找到匹配 (编码问题，跳过详细输出)")
    
    # 测试文本搜索
    print("\n" + "=" * 60)
    print("文本搜索测试")
    print("=" * 60)
    
    test_queries = ["AD1-025", "奥米加", "BT12"]
    for query in test_queries:
        print(f"\n搜索：{query}")
        results = recognizer.search_by_text(query, limit=3)
        for card in results:
            # 安全输出，避免编码问题
            card_name = card.get('card_name', 'N/A').encode('gbk', errors='ignore').decode('gbk')
            pack = card.get('pack', 'N/A').encode('gbk', errors='ignore').decode('gbk')
            print(f"  - {card['card_id']} - {card_name} ({pack})")
    
    recognizer.close()
    print("\n测试完成！")


if __name__ == "__main__":
    project_root = Path(__file__).parent
    test_recognition(project_root)
