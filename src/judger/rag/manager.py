"""
RAG 管理器

核心功能：
- 文档索引和管理
- 智能检索
- 结构化 Prompt 构建
"""
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings

from .types import (
    DocumentType, DocumentSource, DocumentMetadata,
    SearchResult, SearchMode, SearchConfig, ChunkConfig
)
from .embeddings import EmbeddingProvider, create_embedding_provider
from .search import HybridSearchEngine, extract_keywords
from .chunker import DocumentChunker
from .prompt_builder import PromptBuilder


class RAGManager:
    """RAG 系统管理器"""
    
    def __init__(
        self,
        persist_dir: str,
        embedding_provider: Optional[EmbeddingProvider] = None,
        chunk_config: Optional[ChunkConfig] = None,
        search_config: Optional[SearchConfig] = None
    ):
        """
        初始化 RAG 管理器
        
        Args:
            persist_dir: 持久化目录
            embedding_provider: 嵌入提供商
            chunk_config: 分块配置
            search_config: 搜索配置
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化嵌入提供商
        if embedding_provider is None:
            embedding_provider = create_embedding_provider("local")
        self.embedding_provider = embedding_provider
        
        # 初始化配置
        self.chunk_config = chunk_config or ChunkConfig()
        self.search_config = search_config or SearchConfig()
        
        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 初始化组件
        self.chunker = DocumentChunker(self.chunk_config)
        self.search_engine = HybridSearchEngine(self.search_config)
        self.prompt_builder = PromptBuilder()
        
        # 卡牌数据缓存
        self._card_cache: Dict[str, dict] = {}
        self._load_card_cache()
    
    def _load_card_cache(self):
        """加载卡牌数据缓存"""
        # 获取项目根目录
        # 如果 persist_dir 是相对路径，先转换为绝对路径
        persist_abs = self.persist_dir.resolve()
        
        # persist_dir 通常是 .../card_game_judge/data/rag_store
        # 所以向上3级到 card_game_judge，再向上1级到 LLMProject
        card_game_judge_dir = persist_abs.parent.parent  # .../card_game_judge
        project_root = card_game_judge_dir.parent  # .../LLMProject
        
        # 方法1: 尝试加载合并的中文卡牌数据（新路径）
        cn_cards_file = project_root / "digimon_card_data" / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        if cn_cards_file.exists():
            try:
                with open(cn_cards_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_no = card.get('card_no', '').upper()
                        if card_no:
                            self._card_cache[card_no] = card
                print(f"✅ 加载中文卡牌数据: {len(self._card_cache)} 张")
                return
            except Exception as e:
                print(f"⚠️  加载合并卡牌数据失败: {e}")
        
        # 方法2: 尝试旧路径
        cn_cards_file_old = project_root / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        if cn_cards_file_old.exists():
            try:
                with open(cn_cards_file_old, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_no = card.get('card_no', '').upper()
                        if card_no:
                            self._card_cache[card_no] = card
                print(f"✅ 加载中文卡牌数据: {len(self._card_cache)} 张")
                return
            except Exception as e:
                print(f"⚠️  加载旧路径卡牌数据失败: {e}")
        
        # 方法3: 加载分散的卡牌数据文件
        card_data_dir = project_root / "digimon_card_data"
        if card_data_dir.exists():
            try:
                card_files = list(card_data_dir.glob("*_cards.json"))
                
                if card_files:
                    for card_file in card_files:
                        try:
                            with open(card_file, 'r', encoding='utf-8') as f:
                                cards = json.load(f)
                                if isinstance(cards, list):
                                    for card in cards:
                                        card_no = card.get('card_no', '').upper()
                                        if card_no and card_no not in self._card_cache:
                                            self._card_cache[card_no] = card
                        except Exception as e:
                            # 跳过无法加载的文件
                            pass
                    
                    if self._card_cache:
                        print(f"✅ 加载卡牌数据: {len(self._card_cache)} 张")
                        return
            except Exception as e:
                print(f"⚠️  加载分散卡牌数据失败: {e}")
        
        print("⚠️  未找到卡牌数据文件")
    
    def _get_collection_name(self, doc_type: DocumentType) -> str:
        """获取集合名称"""
        return f"dtcg_{doc_type.value}"
    
    def _generate_doc_id(self, content: str, title: str) -> str:
        """生成文档 ID"""
        return hashlib.md5(f"{title}:{content[:100]}".encode()).hexdigest()[:12]
    
    def add_document(
        self,
        content: str,
        metadata: DocumentMetadata
    ) -> Dict:
        """
        添加文档到向量库
        
        Args:
            content: 文档内容
            metadata: 文档元数据
        
        Returns:
            添加结果信息
        """
        # 分块
        chunks = self.chunker.chunk_text(content)
        
        # 生成嵌入
        embeddings = self.embedding_provider.embed_batch(chunks)
        
        # 准备元数据
        collection_name = self._get_collection_name(metadata.doc_type)
        collection = self.client.get_or_create_collection(collection_name)
        
        # 添加到向量库
        ids = [f"{metadata.doc_id}_{i}" for i in range(len(chunks))]
        metadatas = []
        for i in range(len(chunks)):
            meta_dict = {
                "doc_id": metadata.doc_id,
                "title": metadata.title,
                "doc_type": metadata.doc_type.value,
                "source": metadata.source.value,
                "chunk_index": i,
                "created_at": metadata.created_at.isoformat()
            }
            if metadata.version:
                meta_dict["version"] = metadata.version
            if metadata.card_no:
                meta_dict["card_no"] = metadata.card_no
            if metadata.tags:
                meta_dict["tags"] = ",".join(metadata.tags)
            metadatas.append(meta_dict)
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return {
            "doc_id": metadata.doc_id,
            "title": metadata.title,
            "chunk_count": len(chunks),
            "collection": collection_name
        }
    
    def search(
        self,
        query: str,
        doc_types: Optional[List[DocumentType]] = None,
        mode: Optional[SearchMode] = None,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            doc_types: 限定文档类型
            mode: 搜索模式
            top_k: 返回结果数
        
        Returns:
            搜索结果列表
        """
        if doc_types is None:
            doc_types = list(DocumentType)
        if mode is None:
            mode = self.search_config.mode
        if top_k is None:
            top_k = self.search_config.max_results
        
        # 生成查询嵌入
        query_embedding = self.embedding_provider.embed_query(query)
        
        all_results = []
        
        for doc_type in doc_types:
            collection_name = self._get_collection_name(doc_type)
            try:
                collection = self.client.get_collection(collection_name)
            except:
                continue
            
            if mode == SearchMode.VECTOR or mode == SearchMode.HYBRID:
                # 向量搜索
                vector_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 2  # 获取更多候选
                )
                
                for i, (doc_id, distance, doc, metadata) in enumerate(zip(
                    vector_results['ids'][0],
                    vector_results['distances'][0],
                    vector_results['documents'][0],
                    vector_results['metadatas'][0]
                )):
                    score = 1.0 - distance  # 转换为相似度
                    all_results.append((doc_id, score, metadata, doc, 'vector'))
            
            if mode == SearchMode.KEYWORD or mode == SearchMode.HYBRID:
                # 关键词搜索
                keywords = extract_keywords(query)
                if keywords:
                    # 使用 where_document 进行关键词过滤
                    keyword_query = " ".join(keywords)
                    try:
                        keyword_results = collection.query(
                            query_texts=[keyword_query],
                            n_results=top_k * 2
                        )
                        
                        for i, (doc_id, doc, metadata) in enumerate(zip(
                            keyword_results['ids'][0],
                            keyword_results['documents'][0],
                            keyword_results['metadatas'][0]
                        )):
                            # 简单的关键词匹配分数
                            matches = sum(1 for kw in keywords if kw in doc.lower())
                            score = matches / len(keywords) if keywords else 0.0
                            all_results.append((doc_id, score, metadata, doc, 'keyword'))
                    except:
                        pass
        
        # 去重和合并
        seen_ids = set()
        merged_results = []
        for doc_id, score, metadata, doc, search_type in all_results:
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged_results.append((doc_id, score, metadata, doc))
        
        # 重排序
        if self.search_config.enable_rerank:
            merged_results = self.search_engine.rerank(query, merged_results)
        
        # 过滤低分结果
        filtered_results = [
            r for r in merged_results 
            if r[1] >= self.search_config.min_score
        ]
        
        # 转换为 SearchResult
        search_results = []
        for doc_id, score, metadata, doc in filtered_results[:top_k]:
            doc_meta = DocumentMetadata(
                doc_id=metadata.get('doc_id', doc_id),
                title=metadata.get('title', ''),
                doc_type=DocumentType(metadata.get('doc_type', 'rule')),
                source=DocumentSource(metadata.get('source', 'database')),
                version=metadata.get('version'),
                card_no=metadata.get('card_no'),
                tags=metadata.get('tags', '').split(',') if metadata.get('tags') else []
            )
            
            search_results.append(SearchResult(
                content=doc,
                metadata=doc_meta,
                score=score,
                doc_type=doc_meta.doc_type
            ))
        
        return search_results
    
    def search_card_by_number(self, card_no: str) -> Optional[Dict]:
        """
        通过卡号精确搜索卡牌
        
        Args:
            card_no: 卡牌编号
        
        Returns:
            卡牌数据字典
        """
        card_no_upper = card_no.upper()
        
        # 先尝试直接匹配
        if card_no_upper in self._card_cache:
            return self._card_cache[card_no_upper]
        
        # 如果没找到，尝试去掉前导零（EX08-074 -> EX8-074）
        import re
        # 匹配格式：BT01-001, EX08-074 等
        match = re.match(r'^([A-Z]+)0*(\d+)-0*(\d+)$', card_no_upper)
        if match:
            prefix, set_num, card_num = match.groups()
            # 尝试不同的格式组合
            variants = [
                f"{prefix}{set_num}-{card_num}",  # EX8-074
                f"{prefix}{set_num.zfill(2)}-{card_num}",  # EX08-074
                f"{prefix}{set_num}-{card_num.zfill(3)}",  # EX8-074
                f"{prefix}{set_num.zfill(2)}-{card_num.zfill(3)}",  # EX08-074
            ]
            
            for variant in variants:
                if variant in self._card_cache:
                    return self._card_cache[variant]
        
        # 特殊处理 P 系列（P-001, P-1）
        if card_no_upper.startswith('P-'):
            p_match = re.match(r'^P-0*(\d+)$', card_no_upper)
            if p_match:
                card_num = p_match.group(1)
                p_variants = [
                    f"P-{card_num}",
                    f"P-{card_num.zfill(3)}",
                ]
                for variant in p_variants:
                    if variant in self._card_cache:
                        return self._card_cache[variant]
        
        return None
    
    def build_prompt(
        self,
        query: str,
        search_results: List[SearchResult],
        card_data: Optional[List[Dict]] = None
    ) -> str:
        """
        构建结构化 Prompt
        
        Args:
            query: 用户问题
            search_results: 搜索结果
            card_data: 卡牌数据
        
        Returns:
            构建好的 Prompt
        """
        return self.prompt_builder.build(query, search_results, card_data)
    
    def delete_document(self, doc_id: str, doc_type: DocumentType) -> bool:
        """删除文档"""
        collection_name = self._get_collection_name(doc_type)
        try:
            collection = self.client.get_collection(collection_name)
            # 查找所有属于该文档的块
            results = collection.get(where={"doc_id": doc_id})
            if results['ids']:
                collection.delete(ids=results['ids'])
                return True
        except:
            pass
        return False
    
    def list_documents(
        self,
        doc_type: Optional[DocumentType] = None
    ) -> List[Dict]:
        """列出所有文档"""
        doc_types = [doc_type] if doc_type else list(DocumentType)
        documents = {}
        
        for dt in doc_types:
            collection_name = self._get_collection_name(dt)
            try:
                collection = self.client.get_collection(collection_name)
                results = collection.get()
                for meta in results['metadatas']:
                    doc_id = meta.get('doc_id')
                    if doc_id and doc_id not in documents:
                        documents[doc_id] = {
                            "doc_id": doc_id,
                            "title": meta.get('title', ''),
                            "doc_type": meta.get('doc_type', ''),
                            "created_at": meta.get('created_at', ''),
                            "chunk_count": 0
                        }
                    if doc_id:
                        documents[doc_id]["chunk_count"] += 1
            except:
                continue
        
        return list(documents.values())
