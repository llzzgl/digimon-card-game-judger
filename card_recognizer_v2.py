"""
DTCG 卡牌多模态识别系统 v2
改进版：增加特征维度，提升识别准确率
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
from PIL import Image
import numpy as np


class CardRecognizerV2:
    """卡牌识别器 v2 - 改进特征提取"""
    
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
    
    def _extract_color_histogram(self, img) -> np.ndarray:
        """提取颜色直方图"""
        # 转换为 RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 计算每个通道的直方图
        histograms = []
        for channel in range(3):
            hist = img.histogram()[channel*256:(channel+1)*256]
            # 归一化
            total = sum(hist)
            if total > 0:
                hist = [h/total for h in hist]
            histograms.append(hist)
        
        return np.array(histograms).flatten()
    
    def _extract_features(self, image_path: Path) -> Dict:
        """提取图片特征（改进版）"""
        if not image_path.exists():
            return {}
        
        try:
            with Image.open(image_path) as img:
                # 基础特征
                width, height = img.size
                
                # 调整到固定尺寸用于特征提取
                img_resized = img.resize((64, 64), Image.Resampling.LANCZOS)
                img_gray = img_resized.convert('L')
                
                # 亮度特征
                pixels = list(img_gray.getdata())
                avg_brightness = sum(pixels) / len(pixels)
                brightness_std = np.std(pixels)
                
                # 颜色特征
                color_hist = self._extract_color_histogram(img_resized)
                
                # 感知哈希（简化）
                img_small = img_resized.resize((8, 8), Image.Resampling.LANCZOS)
                pixels_small = list(img_small.convert('L').getdata())
                avg = sum(pixels_small) / len(pixels_small)
                phash = ''.join('1' if p > avg else '0' for p in pixels_small)
                
                feature = {
                    'width': width,
                    'height': height,
                    'avg_brightness': avg_brightness,
                    'brightness_std': brightness_std,
                    'color_histogram': color_hist.tolist(),
                    'phash': phash,
                    'phash_int': int(phash, 2)
                }
            
            return feature
        except Exception as e:
            print(f"提取特征失败：{e}")
            return {}
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """计算感知哈希的汉明距离"""
        if len(hash1) != len(hash2):
            return 64  # 最大距离
        
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def _compute_similarity(self, feat1: Dict, feat2: Dict) -> float:
        """计算特征相似度（改进版）"""
        if not feat1 or not feat2:
            return 0.0
        
        score = 0.0
        weights = 0.0
        
        # 1. 感知哈希匹配（权重 40%）
        if 'phash' in feat1 and 'phash' in feat2:
            distance = self._hamming_distance(feat1['phash'], feat2['phash'])
            phash_sim = max(0, 1 - distance/64)
            score += phash_sim * 0.4
            weights += 0.4
        
        # 2. 尺寸匹配（权重 10%）
        if feat1.get('width') == feat2.get('width') and feat1.get('height') == feat2.get('height'):
            score += 0.1
        weights += 0.1
        
        # 3. 亮度相似度（权重 20%）
        if 'avg_brightness' in feat1 and 'avg_brightness' in feat2:
            brightness_diff = abs(feat1['avg_brightness'] - feat2['avg_brightness'])
            brightness_sim = max(0, 1 - brightness_diff/255)
            score += brightness_sim * 0.2
            weights += 0.2
        
        # 4. 颜色直方图相似度（权重 30%）
        if 'color_histogram' in feat1 and 'color_histogram' in feat2:
            hist1 = np.array(feat1['color_histogram'])
            hist2 = np.array(feat2['color_histogram'])
            # 余弦相似度
            dot_product = np.dot(hist1, hist2)
            norm1 = np.linalg.norm(hist1)
            norm2 = np.linalg.norm(hist2)
            if norm1 > 0 and norm2 > 0:
                hist_sim = dot_product / (norm1 * norm2)
                score += hist_sim * 0.3
                weights += 0.3
        
        return score / weights if weights > 0 else 0.0
    
    def recognize(self, image_path: str, top_k: int = 5, threshold: float = 0.6) -> List[Dict]:
        """
        识别卡牌图片（改进版）
        
        Args:
            image_path: 输入图片路径
            top_k: 返回最匹配的 K 个结果
            threshold: 相似度阈值
        
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
        
        results = []
        
        # 1. 精确匹配（哈希完全相同）
        for image_id, info in self.image_features.items():
            if info['image_hash'] == input_hash:
                card_info = self._get_card_info(info['card_id'])
                if card_info:
                    results.append({
                        'card': card_info,
                        'similarity': 1.0,
                        'match_type': 'exact',
                        'image_path': info['image_path']
                    })
        
        # 2. 如果没有精确匹配，使用特征相似度
        if not results:
            print("  未找到精确匹配，使用特征相似度...")
            similarities = []
            
            for image_id, info in self.image_features.items():
                # 加载参考图片特征
                ref_image_path = Path(image_path.parent / Path(info['image_path']).name)
                if ref_image_path.exists():
                    ref_features = self._extract_features(ref_image_path)
                    if ref_features:
                        sim = self._compute_similarity(input_features, ref_features)
                        
                        if sim >= threshold:
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
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'indexed_images': len(self.image_features),
            'total_cards': self.conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        }
    
    def close(self):
        """关闭数据库"""
        self.conn.close()


def test_recognition_v2(project_root: Path):
    """测试 v2 识别功能"""
    print("=" * 60)
    print("DTCG 卡牌识别系统 v2 测试")
    print("=" * 60)
    
    recognizer = CardRecognizerV2(str(project_root / "card_data" / "card_metadata.db"))
    
    # 显示统计
    stats = recognizer.get_stats()
    print(f"\n数据库统计:")
    print(f"  卡牌总数：{stats['total_cards']}")
    print(f"  索引图片：{stats['indexed_images']}")
    
    # 测试图片目录
    test_images_dir = project_root / "card_data" / "images" / "cn" / "raw"
    
    if test_images_dir.exists():
        test_images = list(test_images_dir.glob("*.jpg"))[:5]
        
        print(f"\n测试 {len(test_images)} 张图片识别:")
        
        for img_path in test_images:
            print(f"\n测试图片：{img_path.name}")
            results = recognizer.recognize(str(img_path), top_k=3)
            
            if results:
                print(f"  识别结果：{len(results)} 个匹配")
                for i, result in enumerate(results[:3], 1):
                    card = result['card']
                    print(f"  {i}. {card['card_id']} - {card['card_name'][:30] if card.get('card_name') else 'N/A'}")
                    print(f"     相似度：{result['similarity']:.2f} ({result['match_type']})")
                    print(f"     卡包：{card.get('pack', 'N/A')[:20]} | 稀有度：{card.get('rarity', 'N/A')}")
            else:
                print(f"  [X] 未找到匹配")
    
    recognizer.close()
    print("\n测试完成！")


if __name__ == "__main__":
    project_root = Path(__file__).parent
    test_recognition_v2(project_root)
