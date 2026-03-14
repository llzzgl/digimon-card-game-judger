"""
DTCG 卡牌识别系统 v3 - 鲁棒性增强版
支持：遮挡、反光、小目标、模糊图片识别
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


class RobustCardRecognizer:
    """鲁棒卡牌识别器 v3"""
    
    def __init__(self, db_path: str = "card_data/card_metadata.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.image_features = {}
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
    
    def _preprocess_image(self, img: Image.Image) -> List[Image.Image]:
        """
        图像预处理 - 生成多个增强版本
        
        返回：[原图，增强图 1, 增强图 2, ...]
        """
        enhanced_images = [img]  # 原图
        
        try:
            # 1. 提高对比度（应对模糊）
            enhancer = ImageEnhance.Contrast(img)
            enhanced_images.append(enhancer.enhance(1.5))
            
            # 2. 提高亮度（应对暗光）
            enhancer = ImageEnhance.Brightness(img)
            enhanced_images.append(enhancer.enhance(1.3))
            
            # 3. 锐化（应对模糊）
            enhanced_images.append(img.filter(ImageFilter.SHARPEN))
            
            # 4. 去噪（应对噪点）
            enhanced_images.append(img.filter(ImageFilter.MedianFilter(size=3)))
            
            # 5. 边缘增强（应对轮廓识别）
            enhanced_images.append(img.filter(ImageFilter.EDGE_ENHANCE))
            
        except Exception as e:
            print(f"图像增强失败：{e}")
        
        return enhanced_images
    
    def _extract_features(self, img: Image.Image, robust: bool = True) -> Dict:
        """提取图片特征（鲁棒版）"""
        try:
            width, height = img.size
            
            # 多尺度特征提取
            scales = [(64, 64), (32, 32), (16, 16)]
            all_features = []
            
            for scale in scales:
                img_resized = img.resize(scale, Image.Resampling.LANCZOS)
                img_gray = img_resized.convert('L')
                
                pixels = list(img_gray.getdata())
                avg_brightness = sum(pixels) / len(pixels)
                brightness_std = float(np.std(pixels))
                
                # 感知哈希
                img_small = img_resized.resize((8, 8), Image.Resampling.LANCZOS)
                pixels_small = list(img_small.convert('L').getdata())
                avg = sum(pixels_small) / len(pixels_small)
                phash = ''.join('1' if p > avg else '0' for p in pixels_small)
                
                all_features.append({
                    'scale': scale,
                    'avg_brightness': avg_brightness,
                    'brightness_std': brightness_std,
                    'phash': phash
                })
            
            return {
                'width': width,
                'height': height,
                'multi_scale_features': all_features,
                'primary_phash': all_features[0]['phash']
            }
            
        except Exception as e:
            print(f"提取特征失败：{e}")
            return {}
    
    def _compute_similarity(self, feat1: Dict, feat2: Dict, robust: bool = True) -> float:
        """计算相似度（鲁棒版）"""
        if not feat1 or not feat2:
            return 0.0
        
        score = 0.0
        weights = 0.0
        
        # 多尺度匹配
        if 'multi_scale_features' in feat1 and 'multi_scale_features' in feat2:
            scale_scores = []
            for f1, f2 in zip(feat1['multi_scale_features'], feat2['multi_scale_features']):
                # 感知哈希匹配（64 位）
                distance = sum(c1 != c2 for c1, c2 in zip(f1['phash'], f2['phash']))
                phash_sim = max(0, 1 - distance/64)
                scale_scores.append(phash_sim)
            
            # 取最佳尺度匹配
            best_scale_score = max(scale_scores)
            score += best_scale_score * 0.6
            weights += 0.6
        
        # 尺寸匹配
        if feat1.get('width') == feat2.get('width') and feat1.get('height') == feat2.get('height'):
            score += 0.1
        weights += 0.1
        
        # 亮度相似度（宽容度更大）
        if 'multi_scale_features' in feat1 and 'multi_scale_features' in feat2:
            brightness_diff = abs(feat1['multi_scale_features'][0]['avg_brightness'] - 
                                feat2['multi_scale_features'][0]['avg_brightness'])
            brightness_sim = max(0, 1 - brightness_diff/255)
            score += brightness_sim * 0.3
            weights += 0.3
        
        return score / weights if weights > 0 else 0.0
    
    def recognize(self, image_bytes: bytes, top_k: int = 5, threshold: float = 0.5) -> List[Dict]:
        """
        识别卡牌（鲁棒版）
        
        支持：
        - 部分遮挡
        - 反光
        - 小目标
        - 模糊/不清晰
        
        Args:
            image_bytes: 图片二进制数据
            top_k: 返回数量
            threshold: 相似度阈值（降低到 0.5 提高召回率）
        
        Returns:
            匹配的卡牌列表
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # 预处理：生成多个增强版本
            enhanced_images = self._preprocess_image(img)
            
            all_results = []
            
            # 对每个增强版本进行识别
            for i, enhanced_img in enumerate(enhanced_images):
                input_features = self._extract_features(enhanced_img)
                input_hash = hashlib.md5(image_bytes).hexdigest()
                
                # 精确匹配
                for image_id, info in self.image_features.items():
                    if info['image_hash'] == input_hash:
                        card_info = self._get_card_info(info['card_id'])
                        if card_info:
                            all_results.append({
                                'card': card_info,
                                'similarity': 1.0,
                                'match_type': 'exact',
                                'enhancement': i
                            })
                
                # 模糊匹配
                for image_id, info in self.image_features.items():
                    img_path = PROJECT_ROOT / info['image_path']
                    if img_path.exists():
                        try:
                            with Image.open(img_path) as ref_img:
                                ref_features = self._extract_features(ref_img)
                                if ref_features:
                                    sim = self._compute_similarity(input_features, ref_features)
                                    if sim >= threshold:
                                        card_info = self._get_card_info(info['card_id'])
                                        if card_info:
                                            all_results.append({
                                                'card': card_info,
                                                'similarity': sim,
                                                'match_type': 'fuzzy',
                                                'enhancement': i
                                            })
                        except:
                            pass
            
            # 去重并排序
            seen = set()
            unique_results = []
            for result in all_results:
                card_id = result['card']['card_id']
                if card_id not in seen:
                    seen.add(card_id)
                    unique_results.append(result)
            
            unique_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return unique_results[:top_k]
            
        except Exception as e:
            raise Exception(f"识别失败：{str(e)}")
    
    def _get_card_info(self, card_id: str) -> Optional[Dict]:
        """获取卡牌信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def close(self):
        self.conn.close()


if __name__ == "__main__":
    print("DTCG 卡牌识别系统 v3 - 鲁棒性增强版")
    print("支持：遮挡、反光、小目标、模糊图片")
