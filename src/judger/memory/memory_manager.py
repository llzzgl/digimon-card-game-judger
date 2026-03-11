# -*- coding: utf-8 -*-
"""
记忆管理器 - 负责记忆的存储、检索和管理
参考 openclaw 的记忆持久化设计
"""
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings

from .memory_config import (
    MemoryConfig, MemoryEntry, MemoryType, 
    MemoryImportance, default_memory_config
)
# from .query_processor import query_processor  # 循环依赖，已移除


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """初始化记忆管理器"""
        self.config = config or default_memory_config
        
        # 创建存储目录
        self.storage_path = Path(self.config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化 ChromaDB（用于记忆检索）
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path / "chroma"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建记忆集合
        self.memory_collection = self.client.get_or_create_collection(
            name="verified_memories",
            metadata={"description": "用户验证过的问答记忆"}
        )
        
        # 短期记忆（内存中）
        self.short_term_memories: List[MemoryEntry] = []
        
        # 加载长期记忆索引
        self._load_memory_index()
        
        print(f"[OK] 记忆系统初始化完成")
        print(f"   存储路径: {self.storage_path}")
        print(f"   长期记忆数: {self.memory_collection.count()}")
    
    def _load_memory_index(self):
        """加载记忆索引"""
        try:
            index_file = self.storage_path / "memory_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.memory_index = json.load(f)
            else:
                self.memory_index = {
                    "total_memories": 0,
                    "by_type": {},
                    "by_importance": {},
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"⚠️  加载记忆索引失败: {e}")
            self.memory_index = {"total_memories": 0}
    
    def _save_memory_index(self):
        """保存记忆索引"""
        try:
            index_file = self.storage_path / "memory_index.json"
            self.memory_index["last_updated"] = datetime.now().isoformat()
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存记忆索引失败: {e}")
    
    def _generate_memory_id(self, question: str) -> str:
        """生成记忆ID"""
        timestamp = datetime.now().isoformat()
        content = f"{question}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def add_memory(
        self,
        question: str,
        answer: str,
        summary: str,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        card_numbers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        user_confirmed: bool = False,
        confidence_score: float = 1.0,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """
        添加记忆
        
        Args:
            question: 问题
            answer: 答案
            summary: 总结
            memory_type: 记忆类型
            importance: 重要性
            card_numbers: 相关卡牌编号
            tags: 标签
            user_confirmed: 是否用户确认
            confidence_score: 置信度
            embedding: 嵌入向量
            metadata: 额外的元数据（如修正记忆的错误答案等）
        
        Returns:
            记忆条目
        """
        # 提取卡牌编号（如果未提供）
        if card_numbers is None:
            card_numbers = query_processor.extract_card_numbers(question)
        
        # 生成记忆ID
        memory_id = self._generate_memory_id(question)
        
        # 创建记忆条目
        memory = MemoryEntry(
            id=memory_id,
            question=question,
            answer=answer,
            summary=summary,
            memory_type=memory_type,
            importance=importance,
            card_numbers=card_numbers or [],
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            last_accessed_at=datetime.now().isoformat(),
            access_count=0,
            confidence_score=confidence_score,
            user_confirmed=user_confirmed,
            embedding=embedding
        )
        
        # 如果有额外的元数据，保存到文件中
        if metadata:
            memory.user_feedback = json.dumps(metadata, ensure_ascii=False)
        
        # 根据类型存储
        if memory_type == MemoryType.SHORT_TERM:
            self._add_to_short_term(memory)
        else:
            self._add_to_long_term(memory)
        
        return memory
    
    def _add_to_short_term(self, memory: MemoryEntry):
        """添加到短期记忆"""
        self.short_term_memories.append(memory)
        
        # 限制短期记忆数量
        if len(self.short_term_memories) > self.config.max_short_term_memories:
            # 移除最旧的记忆
            self.short_term_memories.pop(0)
        
        print(f"[MEM] 添加短期记忆: {memory.id}")
    
    def _add_to_long_term(self, memory: MemoryEntry):
        """添加到长期记忆（持久化）"""
        try:
            # 检查是否超过长度限制
            current_count = self.memory_collection.count()
            if current_count >= self.config.max_long_term_memories:
                print(f"⚠️  长期记忆已达上限 ({current_count}/{self.config.max_long_term_memories})")
                print(f"   正在执行记忆整理...")
                self._consolidate_memories()
            
            # 保存到 ChromaDB
            self.memory_collection.add(
                ids=[memory.id],
                documents=[memory.summary],  # 使用总结作为检索文本
                metadatas=[{
                    "question": memory.question,
                    "answer": memory.answer[:500],  # 限制长度
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance.value,
                    "card_numbers": ",".join(memory.card_numbers),
                    "tags": ",".join(memory.tags),
                    "created_at": memory.created_at,
                    "user_confirmed": str(memory.user_confirmed),
                    "confidence_score": memory.confidence_score
                }],
                embeddings=[memory.embedding] if memory.embedding else None
            )
            
            # 保存完整记忆到JSON文件
            memory_file = self.storage_path / f"{memory.id}.json"
            with open(memory_file, 'w', encoding='utf-8') as f:
                memory_dict = {
                    "id": memory.id,
                    "question": memory.question,
                    "answer": memory.answer,
                    "summary": memory.summary,
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance.value,
                    "card_numbers": memory.card_numbers,
                    "tags": memory.tags,
                    "created_at": memory.created_at,
                    "last_accessed_at": memory.last_accessed_at,
                    "access_count": memory.access_count,
                    "confidence_score": memory.confidence_score,
                    "user_confirmed": memory.user_confirmed,
                    "user_feedback": memory.user_feedback
                }
                json.dump(memory_dict, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.memory_index["total_memories"] = self.memory_collection.count()
            self._save_memory_index()
            
            print(f"💾 添加长期记忆: {memory.id}")
            
        except Exception as e:
            print(f"❌ 保存长期记忆失败: {e}")
    
    def _consolidate_memories(self):
        """
        整理记忆：当记忆数量超过上限时，删除低优先级的记忆
        策略：
        1. 保留所有用户确认的记忆
        2. 保留高重要性的记忆
        3. 删除低重要性且访问次数少的记忆
        """
        try:
            print("🔄 开始记忆整理...")
            
            # 获取所有记忆
            all_results = self.memory_collection.get()
            
            if not all_results['ids']:
                return
            
            # 构建记忆评分列表
            memory_scores = []
            for i, memory_id in enumerate(all_results['ids']):
                metadata = all_results['metadatas'][i]
                
                # 计算评分
                importance = int(metadata.get('importance', 2))
                user_confirmed = metadata.get('user_confirmed', 'False') == 'True'
                
                # 读取访问次数
                access_count = 0
                try:
                    memory_file = self.storage_path / f"{memory_id}.json"
                    if memory_file.exists():
                        with open(memory_file, 'r', encoding='utf-8') as f:
                            memory_data = json.load(f)
                            access_count = memory_data.get('access_count', 0)
                except:
                    pass
                
                # 评分规则：
                # - 用户确认的记忆：+100分
                # - 重要性：importance * 10
                # - 访问次数：access_count * 2
                score = 0
                if user_confirmed:
                    score += 100
                score += importance * 10
                score += access_count * 2
                
                memory_scores.append({
                    'id': memory_id,
                    'score': score,
                    'user_confirmed': user_confirmed,
                    'importance': importance
                })
            
            # 按评分排序
            memory_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # 计算需要删除的数量
            target_count = int(self.config.max_long_term_memories * 0.8)  # 保留80%
            to_delete_count = len(memory_scores) - target_count
            
            if to_delete_count <= 0:
                print("   无需删除记忆")
                return
            
            # 删除低分记忆
            deleted_count = 0
            for memory_info in memory_scores[-to_delete_count:]:
                memory_id = memory_info['id']
                
                # 删除 ChromaDB 中的记忆
                try:
                    self.memory_collection.delete(ids=[memory_id])
                    
                    # 删除 JSON 文件
                    memory_file = self.storage_path / f"{memory_id}.json"
                    if memory_file.exists():
                        memory_file.unlink()
                    
                    deleted_count += 1
                except Exception as e:
                    print(f"   删除记忆 {memory_id} 失败: {e}")
            
            print(f"[OK] 记忆整理完成：删除 {deleted_count} 条低优先级记忆")
            print(f"   当前记忆数: {self.memory_collection.count()}")
            
        except Exception as e:
            print(f"❌ 记忆整理失败: {e}")
            import traceback
            traceback.print_exc()
    
    def search_memories(
        self,
        query: str,
        top_k: Optional[int] = None,
        memory_type: Optional[MemoryType] = None,
        min_importance: Optional[MemoryImportance] = None
    ) -> List[Dict]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            memory_type: 限定记忆类型
            min_importance: 最小重要性
        
        Returns:
            记忆列表
        """
        if not self.config.enable_memory_search:
            return []
        
        top_k = top_k or self.config.memory_search_top_k
        
        try:
            # 构建过滤条件
            where_filter = {}
            if memory_type:
                where_filter["memory_type"] = memory_type.value
            if min_importance:
                where_filter["importance"] = {"$gte": min_importance.value}
            
            # 搜索
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter if where_filter else None
            )
            
            # 格式化结果
            memories = []
            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1.0 - distance
                    
                    # 过滤低相似度结果
                    if similarity < self.config.memory_similarity_threshold:
                        continue
                    
                    metadata = results['metadatas'][0][i]
                    document = results['documents'][0][i]
                    
                    memories.append({
                        "id": memory_id,
                        "question": metadata.get("question", ""),
                        "answer": metadata.get("answer", ""),
                        "summary": document,
                        "similarity": similarity,
                        "importance": metadata.get("importance", 2),
                        "card_numbers": metadata.get("card_numbers", "").split(","),
                        "user_confirmed": metadata.get("user_confirmed", "False") == "True"
                    })
                    
                    # 更新访问统计
                    self._update_access_stats(memory_id)
            
            return memories
            
        except Exception as e:
            print(f"❌ 搜索记忆失败: {e}")
            return []
    
    def _update_access_stats(self, memory_id: str):
        """更新记忆访问统计"""
        try:
            memory_file = self.storage_path / f"{memory_id}.json"
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                memory_data["access_count"] = memory_data.get("access_count", 0) + 1
                memory_data["last_accessed_at"] = datetime.now().isoformat()
                
                with open(memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  更新访问统计失败: {e}")
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """获取完整记忆"""
        try:
            memory_file = self.storage_path / f"{memory_id}.json"
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ 获取记忆失败: {e}")
        return None
    
    def update_memory_feedback(
        self,
        memory_id: str,
        user_confirmed: bool,
        user_feedback: Optional[str] = None
    ) -> bool:
        """更新记忆的用户反馈"""
        try:
            memory_file = self.storage_path / f"{memory_id}.json"
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                memory_data["user_confirmed"] = user_confirmed
                memory_data["user_feedback"] = user_feedback
                
                with open(memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
                # 同时更新 ChromaDB 中的元数据
                self.memory_collection.update(
                    ids=[memory_id],
                    metadatas=[{
                        **memory_data,
                        "user_confirmed": str(user_confirmed)
                    }]
                )
                
                return True
        except Exception as e:
            print(f"❌ 更新反馈失败: {e}")
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            # 从 ChromaDB 删除
            self.memory_collection.delete(ids=[memory_id])
            
            # 删除文件
            memory_file = self.storage_path / f"{memory_id}.json"
            if memory_file.exists():
                memory_file.unlink()
            
            # 更新索引
            self.memory_index["total_memories"] = self.memory_collection.count()
            self._save_memory_index()
            
            print(f"🗑️  删除记忆: {memory_id}")
            return True
        except Exception as e:
            print(f"❌ 删除记忆失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "total_memories": self.memory_collection.count(),
            "short_term_memories": len(self.short_term_memories),
            "storage_path": str(self.storage_path),
            "last_updated": self.memory_index.get("last_updated", ""),
            "config": {
                "max_short_term": self.config.max_short_term_memories,
                "max_long_term": self.config.max_long_term_memories,
                "search_enabled": self.config.enable_memory_search,
                "auto_summarize": self.config.enable_auto_summarize
            }
        }


# 全局实例
memory_manager = MemoryManager()

