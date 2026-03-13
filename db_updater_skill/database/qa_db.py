"""
QA 数据库管理
"""

import json
import os
from pathlib import Path
from datetime import datetime


class QADatabase:
    """QA 数据库管理类"""
    
    def __init__(self):
        self.qas = []
        self.qa_index = {}  # id -> qa
        
    def load_from_folder(self, folder_path):
        """
        从文件夹加载 QA 数据
        
        Args:
            folder_path: 包含 QA JSON 文件的文件夹路径
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            print(f"⚠ 文件夹不存在：{folder_path}")
            return
        
        print(f"\n从 {folder_path} 加载 QA 数据...")
        
        # 查找所有 QA JSON 文件
        json_files = list(folder_path.glob("official_qa_*.json"))
        
        total_qas = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    qas = json.load(f)
                    if isinstance(qas, list):
                        self.qas.extend(qas)
                        total_qas += len(qas)
                        print(f"  ✓ {json_file.name}: {len(qas)} 条 QA")
            except Exception as e:
                print(f"  ✗ {json_file.name} 加载失败：{e}")
        
        print(f"✓ 共加载 {total_qas} 条 QA")
        
        # 构建索引
        self._build_index()
    
    def _build_index(self):
        """构建 QA 索引"""
        self.qa_index = {}
        for qa in self.qas:
            qa_id = qa.get('id')
            if qa_id:
                self.qa_index[qa_id] = qa
    
    def merge_and_deduplicate(self):
        """合并并去重"""
        print("\n合并并去重 QA 数据...")
        
        # 使用索引去重（后加载的覆盖先加载的）
        unique_qas = {}
        for qa in self.qas:
            qa_id = qa.get('id')
            if qa_id:
                unique_qas[qa_id] = qa
        
        self.qas = list(unique_qas.values())
        self._build_index()
        
        print(f"✓ 去重后剩余 {len(self.qas)} 条 QA")
    
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
            json.dump(self.qas, f, ensure_ascii=False, indent=2)
        
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ 保存完成 ({file_size:.2f} MB)")
    
    def search_by_id(self, qa_id):
        """根据 QA ID 搜索"""
        return self.qa_index.get(qa_id)
    
    def search_by_keyword(self, keyword):
        """根据关键词搜索（模糊匹配）"""
        results = []
        keyword_lower = keyword.lower()
        
        for qa in self.qas:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            
            if keyword_lower in question.lower() or keyword_lower in answer.lower():
                results.append(qa)
        
        return results
    
    def search_by_card(self, card_name_or_no):
        """根据卡牌名称或编号搜索相关 QA"""
        results = []
        keyword = card_name_or_no.lower()
        
        for qa in self.qas:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            card_name = qa.get('card_name', '')
            card_no = qa.get('card_no', '')
            
            # 在问题、答案、卡牌名称、卡牌编号中搜索
            if (keyword in question.lower() or 
                keyword in answer.lower() or
                keyword in card_name.lower() or
                keyword in card_no.lower()):
                results.append(qa)
        
        return results
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            "total_qas": len(self.qas),
            "unique_ids": len(self.qa_index),
            "by_language": {},
            "with_card_info": 0,
        }
        
        for qa in self.qas:
            # 按语言统计
            language = qa.get('language', 'unknown')
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1
            
            # 统计有卡牌信息的 QA
            if qa.get('card_name') or qa.get('card_no'):
                stats["with_card_info"] += 1
        
        return stats


if __name__ == "__main__":
    # 测试
    db = QADatabase()
    db.load_from_folder("../../card_game_judge/card_game_QA_manger")
    db.merge_and_deduplicate()
    db.save_to_json("../../skill/data/rulings.json")
    
    print("\n统计信息:")
    stats = db.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
