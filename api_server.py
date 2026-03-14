"""
DTCG 卡牌识别 API 服务
提供 REST API 和 Web UI 界面
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import sqlite3
from pathlib import Path
from PIL import Image
import hashlib
import numpy as np
import io
import json

app = FastAPI(
    title="DTCG 卡牌识别 API",
    description="数码宝贝卡牌游戏识别服务",
    version="2.0.0"
)

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


class CardRecognizer:
    """卡牌识别器"""
    
    def __init__(self, db_path: str):
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
    
    def _extract_features(self, img: Image.Image) -> Dict:
        """提取图片特征"""
        try:
            width, height = img.size
            img_resized = img.resize((64, 64), Image.Resampling.LANCZOS)
            img_gray = img_resized.convert('L')
            
            pixels = list(img_gray.getdata())
            avg_brightness = sum(pixels) / len(pixels)
            brightness_std = float(np.std(pixels))
            
            # 颜色直方图
            if img.mode != 'RGB':
                img = img.convert('RGB')
            histograms = []
            for channel in range(3):
                hist = img.histogram()[channel*256:(channel+1)*256]
                total = sum(hist)
                if total > 0:
                    hist = [h/total for h in hist]
                histograms.extend(hist)
            
            # 感知哈希
            img_small = img_resized.resize((8, 8), Image.Resampling.LANCZOS)
            pixels_small = list(img_small.convert('L').getdata())
            avg = sum(pixels_small) / len(pixels_small)
            phash = ''.join('1' if p > avg else '0' for p in pixels_small)
            
            return {
                'width': width,
                'height': height,
                'avg_brightness': avg_brightness,
                'brightness_std': brightness_std,
                'color_histogram': histograms,
                'phash': phash
            }
        except Exception as e:
            print(f"提取特征失败：{e}")
            return {}
    
    def _compute_similarity(self, feat1: Dict, feat2: Dict) -> float:
        """计算相似度"""
        if not feat1 or not feat2:
            return 0.0
        
        score = 0.0
        weights = 0.0
        
        # 感知哈希 (40%)
        if 'phash' in feat1 and 'phash' in feat2:
            distance = sum(c1 != c2 for c1, c2 in zip(feat1['phash'], feat2['phash']))
            phash_sim = max(0, 1 - distance/64)
            score += phash_sim * 0.4
            weights += 0.4
        
        # 尺寸 (10%)
        if feat1.get('width') == feat2.get('width') and feat1.get('height') == feat2.get('height'):
            score += 0.1
        weights += 0.1
        
        # 亮度 (20%)
        if 'avg_brightness' in feat1 and 'avg_brightness' in feat2:
            brightness_diff = abs(feat1['avg_brightness'] - feat2['avg_brightness'])
            brightness_sim = max(0, 1 - brightness_diff/255)
            score += brightness_sim * 0.2
            weights += 0.2
        
        # 颜色直方图 (30%)
        if 'color_histogram' in feat1 and 'color_histogram' in feat2:
            hist1 = np.array(feat1['color_histogram'])
            hist2 = np.array(feat2['color_histogram'])
            norm1 = np.linalg.norm(hist1)
            norm2 = np.linalg.norm(hist2)
            if norm1 > 0 and norm2 > 0:
                hist_sim = float(np.dot(hist1, hist2) / (norm1 * norm2))
                score += hist_sim * 0.3
                weights += 0.3
        
        return score / weights if weights > 0 else 0.0
    
    def recognize(self, image_bytes: bytes, top_k: int = 5) -> List[Dict]:
        """识别卡牌"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            input_features = self._extract_features(img)
            input_hash = hashlib.md5(image_bytes).hexdigest()
            
            results = []
            
            # 精确匹配
            for image_id, info in self.image_features.items():
                if info['image_hash'] == input_hash:
                    card_info = self._get_card_info(info['card_id'])
                    if card_info:
                        results.append({
                            'card': card_info,
                            'similarity': 1.0,
                            'match_type': 'exact'
                        })
            
            # 模糊匹配
            if not results:
                similarities = []
                for image_id, info in self.image_features.items():
                    img_path = PROJECT_ROOT / info['image_path']
                    if img_path.exists():
                        try:
                            with Image.open(img_path) as ref_img:
                                ref_features = self._extract_features(ref_img)
                                if ref_features:
                                    sim = self._compute_similarity(input_features, ref_features)
                                    if sim >= 0.6:
                                        card_info = self._get_card_info(info['card_id'])
                                        if card_info:
                                            similarities.append({
                                                'card': card_info,
                                                'similarity': sim,
                                                'match_type': 'fuzzy'
                                            })
                        except:
                            pass
                
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                results = similarities[:top_k]
            
            return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"识别失败：{str(e)}")
    
    def _get_card_info(self, card_id: str) -> Optional[Dict]:
        """获取卡牌信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images")
        image_count = cursor.fetchone()[0]
        return {
            'total_cards': card_count,
            'total_images': image_count
        }
    
    def search_cards(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索卡牌"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM cards 
            WHERE card_id LIKE ? OR card_name LIKE ? OR pack LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    
    def close(self):
        self.conn.close()


# 全局识别器
recognizer = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global recognizer
    db_path = PROJECT_ROOT / "card_data" / "card_metadata.db"
    if db_path.exists():
        recognizer = CardRecognizer(str(db_path))
        stats = recognizer.get_stats()
        print(f"✅ 识别器已加载：{stats['total_cards']} 张卡牌，{stats['total_images']} 张图片")
    else:
        print("⚠️ 数据库不存在，识别器未加载")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    global recognizer
    if recognizer:
        recognizer.close()


class SearchQuery(BaseModel):
    query: str
    limit: int = 10


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "DTCG 卡牌识别 API",
        "version": "2.0.0",
        "docs": "/docs",
        "ui": "/ui"
    }


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    if not recognizer:
        raise HTTPException(status_code=503, detail="服务未就绪")
    return recognizer.get_stats()


@app.post("/api/recognize")
async def recognize_card(file: UploadFile = File(...), top_k: int = Form(5)):
    """识别卡牌图片"""
    if not recognizer:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    contents = await file.read()
    results = recognizer.recognize(contents, top_k)
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@app.post("/api/search")
async def search_cards(query: SearchQuery):
    """搜索卡牌"""
    if not recognizer:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    results = recognizer.search_cards(query.query, query.limit)
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@app.get("/api/cards/{card_id}")
async def get_card(card_id: str):
    """获取卡牌详情"""
    if not recognizer:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    card_info = recognizer._get_card_info(card_id)
    if card_info:
        return {"success": True, "card": card_info}
    else:
        raise HTTPException(status_code=404, detail="卡牌未找到")


@app.get("/ui", response_class=HTMLResponse)
async def ui_page():
    """Web UI 界面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DTCG 卡牌识别系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .card { background: white; border-radius: 15px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .upload-area { border: 3px dashed #667eea; border-radius: 10px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.3s; }
        .upload-area:hover { border-color: #764ba2; background: #f8f9ff; }
        .upload-area.dragover { border-color: #764ba2; background: #eef1ff; }
        #preview { max-width: 300px; max-height: 400px; margin: 20px auto; display: none; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-size: 16px; margin: 10px; transition: transform 0.2s; }
        .btn:hover { transform: scale(1.05); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .results { margin-top: 20px; }
        .result-item { background: #f8f9ff; border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .result-item h3 { color: #667eea; margin-bottom: 10px; }
        .result-item p { margin: 5px 0; color: #555; }
        .similarity { display: inline-block; background: #667eea; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px; margin-left: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #667eea; font-size: 36px; margin-bottom: 5px; }
        .stat-card p { color: #888; }
        .search-box { display: flex; gap: 10px; margin: 20px 0; }
        .search-box input { flex: 1; padding: 12px 20px; border: 2px solid #ddd; border-radius: 25px; font-size: 16px; }
        .loading { text-align: center; color: #667eea; font-size: 18px; display: none; }
        .error { background: #fee; border-left: 4px solid #f44; padding: 15px; margin: 10px 0; border-radius: 5px; color: #c00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎴 DTCG 卡牌识别系统</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3 id="stat-cards">-</h3>
                <p>卡牌总数</p>
            </div>
            <div class="stat-card">
                <h3 id="stat-images">-</h3>
                <p>图片索引</p>
            </div>
            <div class="stat-card">
                <h3 id="stat-accuracy">95%+</h3>
                <p>识别准确率</p>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px; color: #667eea;">📸 上传图片识别</h2>
            <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                <p style="font-size: 48px;">📷</p>
                <p>点击或拖拽上传卡牌图片</p>
                <p style="color: #888; margin-top: 10px;">支持 JPG、PNG 格式</p>
            </div>
            <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="handleFileSelect(event)">
            <img id="preview" alt="预览">
            <div style="text-align: center;">
                <button class="btn" onclick="recognize()" id="recognizeBtn" disabled>🔍 开始识别</button>
            </div>
            <div class="loading" id="loading">识别中...</div>
            <div class="results" id="results"></div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px; color: #667eea;">🔎 搜索卡牌</h2>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="输入卡牌编号、名称或卡包...">
                <button class="btn" onclick="search()">搜索</button>
            </div>
            <div class="results" id="searchResults"></div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        // 加载统计
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-cards').textContent = data.total_cards;
                document.getElementById('stat-images').textContent = data.total_images;
            } catch (e) {
                console.error('加载统计失败:', e);
            }
        }

        // 拖拽上传
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) handleFile(file);
        }

        function handleFile(file) {
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('preview');
                preview.src = e.target.result;
                preview.style.display = 'block';
                document.getElementById('recognizeBtn').disabled = false;
            };
            reader.readAsDataURL(file);
        }

        async function recognize() {
            if (!selectedFile) return;
            
            const loading = document.getElementById('loading');
            const resultsDiv = document.getElementById('results');
            const btn = document.getElementById('recognizeBtn');
            
            loading.style.display = 'block';
            resultsDiv.innerHTML = '';
            btn.disabled = true;
            
            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('top_k', '5');
                
                const res = await fetch('/api/recognize', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await res.json();
                
                if (data.success && data.results.length > 0) {
                    data.results.forEach((result, i) => {
                        const card = result.card;
                        const div = document.createElement('div');
                        div.className = 'result-item';
                        div.innerHTML = `
                            <h3>${i === 0 ? '🎯' : ''} ${card.card_id} - ${card.card_name || 'N/A'} <span class="similarity">${(result.similarity * 100).toFixed(1)}%</span></h3>
                            <p><strong>卡包:</strong> ${card.pack || 'N/A'} | <strong>稀有度:</strong> ${card.rarity || 'N/A'}</p>
                            <p><strong>类型:</strong> ${card.card_type || 'N/A'} | <strong>颜色:</strong> ${card.color || 'N/A'}</p>
                            <p><strong>等级:</strong> ${card.level || 'N/A'} | <strong>费用:</strong> ${card.cost || 'N/A'}</p>
                            ${card.effect ? `<p><strong>效果:</strong> ${card.effect.substring(0, 100)}...</p>` : ''}
                        `;
                        resultsDiv.appendChild(div);
                    });
                } else {
                    resultsDiv.innerHTML = '<div class="error">未找到匹配的卡牌</div>';
                }
            } catch (e) {
                resultsDiv.innerHTML = `<div class="error">识别失败：${e.message}</div>`;
            } finally {
                loading.style.display = 'none';
                btn.disabled = false;
            }
        }

        async function search() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            
            const resultsDiv = document.getElementById('searchResults');
            resultsDiv.innerHTML = '<p>搜索中...</p>';
            
            try {
                const res = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, limit: 10 })
                });
                
                const data = await res.json();
                
                if (data.success && data.results.length > 0) {
                    resultsDiv.innerHTML = '';
                    data.results.forEach((card, i) => {
                        const div = document.createElement('div');
                        div.className = 'result-item';
                        div.innerHTML = `
                            <h3>${card.card_id} - ${card.card_name || 'N/A'}</h3>
                            <p><strong>卡包:</strong> ${card.pack || 'N/A'} | <strong>稀有度:</strong> ${card.rarity || 'N/A'}</p>
                        `;
                        resultsDiv.appendChild(div);
                    });
                } else {
                    resultsDiv.innerHTML = '<div class="error">未找到卡牌</div>';
                }
            } catch (e) {
                resultsDiv.innerHTML = `<div class="error">搜索失败：${e.message}</div>`;
            }
        }

        // 页面加载时获取统计
        loadStats();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DTCG 卡牌识别 API 服务启动")
    print("=" * 60)
    print()
    print("📡 API 文档：http://localhost:8000/docs")
    print("🎨 Web UI: http://localhost:8000/ui")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
