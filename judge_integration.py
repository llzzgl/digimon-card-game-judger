"""
DTCG 裁判系统集成 - 卡牌识别 + 裁定询问
将卡牌识别功能整合到 card_game_judge 裁判系统
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import io
from PIL import Image
from typing import Dict, List, Optional


class JudgeWithRecognition:
    """带识别功能的裁判系统"""
    
    def __init__(self):
        self.db_path = PROJECT_ROOT / "card_data" / "card_metadata.db"
        self.conn = sqlite3.connect(self.db_path)
        self.rulings_db = PROJECT_ROOT / "card_data" / "rulings.json"
    
    def recognize_card(self, image_bytes: bytes) -> List[Dict]:
        """识别卡牌"""
        # 调用识别器
        from card_recognizer_v3_robust import RobustCardRecognizer
        recognizer = RobustCardRecognizer(str(self.db_path))
        results = recognizer.recognize(image_bytes, top_k=5)
        recognizer.close()
        return results
    
    def get_card_rulings(self, card_id: str) -> List[Dict]:
        """获取卡牌裁定"""
        # 从裁定数据库查询
        if self.rulings_db.exists():
            import json
            with open(self.rulings_db, 'r', encoding='utf-8') as f:
                rulings = json.load(f)
            
            # 查找相关裁定
            card_rulings = []
            for ruling in rulings:
                if card_id in ruling.get('card_id', ''):
                    card_rulings.append(ruling)
            
            return card_rulings
        return []
    
    def answer_card_question(self, card_id: str, question: str) -> Dict:
        """
        回答卡牌相关问题
        
        Args:
            card_id: 卡牌 ID
            question: 问题（如"这张卡的效果是什么？"）
        
        Returns:
            回答
        """
        # 获取卡牌信息
        card_info = self._get_card_info(card_id)
        
        if not card_info:
            return {
                "success": False,
                "error": "未找到卡牌信息"
            }
        
        # 获取裁定
        rulings = self.get_card_rulings(card_id)
        
        # 生成回答
        answer = {
            "success": True,
            "card": card_info,
            "question": question,
            "answer": self._generate_answer(card_info, question),
            "rulings": rulings
        }
        
        return answer
    
    def _generate_answer(self, card_info: Dict, question: str) -> str:
        """生成回答"""
        question_lower = question.lower()
        
        if "效果" in question or "effect" in question_lower:
            effect = card_info.get('effect', '无效果信息')
            return f"{card_info.get('card_name', card_info.get('card_id'))} 的效果：\n{effect}"
        
        elif "费用" in question or "cost" in question_lower:
            cost = card_info.get('cost', '未知')
            return f"{card_info.get('card_name', card_info.get('card_id'))} 的费用是：{cost}"
        
        elif "进化" in question or "digivolve" in question_lower:
            evolve_cost = card_info.get('digivolve_cost1', '未知')
            return f"{card_info.get('card_name', card_info.get('card_id'))} 的进化费用：{evolve_cost}"
        
        else:
            # 默认返回卡牌基本信息
            return f"""
{card_info.get('card_name', card_info.get('card_id'))}

卡包：{card_info.get('pack', '未知')}
稀有度：{card_info.get('rarity', '未知')}
类型：{card_info.get('card_type', '未知')}
颜色：{card_info.get('color', '未知')}
等级：{card_info.get('level', '未知')}
费用：{card_info.get('cost', '未知')}
DP: {card_info.get('dp', '未知')}

效果：
{card_info.get('effect', '无效果信息')}
"""
    
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


def create_judge_api() -> FastAPI:
    """创建裁判 API"""
    app = FastAPI(
        title="DTCG 裁判系统 - 集成版",
        description="卡牌识别 + 裁定询问",
        version="3.0.0"
    )
    
    judge = JudgeWithRecognition()
    
    @app.on_event("shutdown")
    async def shutdown():
        judge.close()
    
    @app.post("/api/judge/recognize_and_ask")
    async def recognize_and_ask(
        file: UploadFile = File(...),
        question: str = Form(...)
    ):
        """
        上传图片并询问
        
        流程：
        1. 识别卡牌
        2. 根据问题检索裁定
        3. 返回回答
        """
        try:
            # 识别卡牌
            contents = await file.read()
            recognition_results = judge.recognize_card(contents)
            
            if not recognition_results:
                return {
                    "success": False,
                    "error": "未识别到卡牌"
                }
            
            # 使用最佳匹配
            best_match = recognition_results[0]
            card_id = best_match['card']['card_id']
            
            # 回答问题
            answer = judge.answer_card_question(card_id, question)
            
            return {
                "success": True,
                "recognition": {
                    "card_id": card_id,
                    "similarity": best_match['similarity'],
                    "match_type": best_match['match_type']
                },
                "answer": answer
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/judge/rulings/{card_id}")
    async def get_rulings(card_id: str):
        """获取卡牌裁定"""
        rulings = judge.get_card_rulings(card_id)
        return {
            "success": True,
            "card_id": card_id,
            "rulings": rulings,
            "count": len(rulings)
        }
    
    return app


if __name__ == "__main__":
    print("DTCG 裁判系统集成模块")
    print("功能：卡牌识别 + 裁定询问")
