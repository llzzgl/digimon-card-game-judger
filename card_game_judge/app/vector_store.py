# 在导入任何库之前设置环境变量和抑制警告
import warnings
import os
import json
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*CryptographyDeprecationWarning.*")
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*telemetry.*")

# 在导入 chromadb 之前禁用遥测
from chromadb.config import Settings
import chromadb

from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from typing import List, Optional, Dict
import hashlib
from datetime import datetime

from app.config import (
    CHROMA_PERSIST_DIR, EMBEDDING_MODEL, OPENAI_API_KEY,
    CHUNK_SIZE, CHUNK_OVERLAP
)
from app.models import DocumentType, DocumentMetadata

# 中文卡牌数据路径
CN_CARDS_FILE = Path(__file__).parent.parent.parent / "digimon_card_data_chiness" / "digimon_cards_cn.json"


class VectorStoreManager:
    def __init__(self):
        self._embeddings = None  # 延迟加载
        self._cn_cards: Dict[str, dict] = {}  # 中文卡牌数据缓存 {card_no: card_data}
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", " ", ""]
        )
        self._load_cn_cards()
    
    def _load_cn_cards(self):
        """加载中文卡牌数据"""
        if CN_CARDS_FILE.exists():
            try:
                with open(CN_CARDS_FILE, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_no = card.get('card_no', '').upper()
                        if card_no:
                            self._cn_cards[card_no] = card
                print(f"✅ [卡牌数据] 加载中文卡牌数据成功: {len(self._cn_cards)} 张")
            except Exception as e:
                print(f"❌ [卡牌数据] 加载中文卡牌失败: {e}")
        else:
            print(f"❌ [卡牌数据] 中文卡牌文件不存在: {CN_CARDS_FILE}")
    
    def get_cn_card(self, card_no: str) -> Optional[dict]:
        """获取中文卡牌数据"""
        return self._cn_cards.get(card_no.upper())
    
    def format_cn_card(self, card: dict) -> str:
        """格式化中文卡牌数据为文本"""
        parts = []
        parts.append(f"卡牌编号: {card.get('card_no', '')}")
        parts.append(f"中文名: {card.get('name_cn', '')}")
        parts.append(f"日文名: {card.get('name_jp', '')}")
        parts.append(f"类型: {card.get('type', '')}")
        parts.append(f"稀有度: {card.get('rarity', '')}")
        parts.append(f"颜色: {card.get('color', '')}")
        if card.get('level'):
            parts.append(f"等级: Lv.{card.get('level')}")
        if card.get('play_cost'):
            parts.append(f"登场费用: {card.get('play_cost')}")
        if card.get('dp') and card.get('dp') != '-':
            parts.append(f"DP: {card.get('dp')}")
        if card.get('form'):
            parts.append(f"形态: {card.get('form')}")
        if card.get('attribute'):
            parts.append(f"属性: {card.get('attribute')}")
        if card.get('species'):
            parts.append(f"类型: {card.get('species')}")
        if card.get('evolution_condition'):
            parts.append(f"进化条件: {card.get('evolution_condition')}")
        if card.get('effect'):
            parts.append(f"效果: {card.get('effect')}")
        if card.get('inherited_effect'):
            parts.append(f"继承效果: {card.get('inherited_effect')}")
        if card.get('security_effect'):
            parts.append(f"安防效果: {card.get('security_effect')}")
        return "\n".join(parts)
    
    @property
    def embeddings(self):
        """延迟加载 embedding 模型"""
        if self._embeddings is None:
            self._embeddings = self._init_embeddings()
        return self._embeddings
    
    def _init_embeddings(self):
        if EMBEDDING_MODEL == "local":
            # 使用多语言 Embedding 模型，支持中日英
            return HuggingFaceEmbeddings(
                model_name="BAAI/bge-m3",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        else:
            return OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    def _get_collection_name(self, doc_type: DocumentType) -> str:
        return f"card_game_{doc_type.value}"
    
    def _generate_doc_id(self, content: str, title: str) -> str:
        return hashlib.md5(f"{title}:{content[:100]}".encode()).hexdigest()[:12]

    def add_document(self, content: str, metadata: DocumentMetadata) -> dict:
        """添加文档到向量库"""
        collection_name = self._get_collection_name(metadata.doc_type)
        doc_id = self._generate_doc_id(content, metadata.title)
        
        # 切分文档
        chunks = self.text_splitter.split_text(content)
        
        # 准备元数据
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "doc_id": doc_id,
                "title": metadata.title,
                "doc_type": metadata.doc_type.value,
                "version": metadata.version or "",
                "effective_date": metadata.effective_date or "",
                "source": metadata.source or "",
                "tags": ",".join(metadata.tags),
                "chunk_index": i,
                "created_at": datetime.now().isoformat()
            })
        
        # 获取或创建 collection
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        # 添加文档
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        vectorstore.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
        
        return {
            "doc_id": doc_id,
            "title": metadata.title,
            "chunk_count": len(chunks),
            "collection": collection_name
        }
    
    def search(
        self, 
        query: str, 
        doc_types: Optional[List[DocumentType]] = None,
        top_k: int = 5,
        translate_query: bool = False,  # 默认不翻译查询
        translate_result: bool = True   # 默认翻译结果
    ) -> List[dict]:
        """
        跨集合搜索
        
        Args:
            query: 查询文本
            doc_types: 限定搜索的文档类型
            top_k: 返回结果数量
            translate_query: 是否将中文查询扩展为中日双语（已废弃，默认False）
            translate_result: 是否将返回结果中的日文术语翻译为中文
        """
        from app.terminology_translator import terminology_translator
        
        if doc_types is None:
            doc_types = list(DocumentType)
        
        # 不再扩展查询，直接使用原始查询
        search_query = query
        
        all_results = []
        for doc_type in doc_types:
            collection_name = self._get_collection_name(doc_type)
            try:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=CHROMA_PERSIST_DIR
                )
                results = vectorstore.similarity_search_with_score(search_query, k=top_k)
                for doc, score in results:
                    content = doc.page_content
                    # 将返回结果中的日文术语翻译为中文
                    if translate_result:
                        content = terminology_translator.translate_result_to_chinese(content)
                    
                    all_results.append({
                        "content": content,
                        "content_original": doc.page_content,  # 保留原始内容
                        "metadata": doc.metadata,
                        "score": float(score),
                        "doc_type": doc_type.value
                    })
            except Exception:
                continue
        
        # 按相似度排序
        all_results.sort(key=lambda x: x["score"])
        return all_results[:top_k]
    
    def search_by_card_number(self, card_no: str, translate_result: bool = True) -> List[dict]:
        """
        通过卡牌编号精确搜索
        优先从中文卡牌数据中查找
        """
        results = []
        card_no_upper = card_no.upper()
        
        print(f"[卡牌搜索] 搜索卡牌: {card_no_upper}")
        
        # 优先从中文卡牌数据中查找
        cn_card = self.get_cn_card(card_no_upper)
        if cn_card:
            content = self.format_cn_card(cn_card)
            results.append({
                "content": content,
                "content_original": content,
                "metadata": {
                    "title": f"{cn_card.get('card_no', '')} {cn_card.get('name_cn', '')}",
                    "doc_type": "card",
                    "card_no": cn_card.get('card_no', ''),
                    "source": "cn_cards"
                },
                "score": 0.0,  # 精确匹配
                "doc_type": "card"
            })
            print(f"[卡牌搜索] 从中文数据找到: {card_no_upper} - {cn_card.get('name_cn', '')}")
            return results
        
        # 如果中文数据没有，回退到向量库搜索
        print(f"[卡牌搜索] 中文数据未找到 {card_no_upper}，尝试向量库...")
        from app.terminology_translator import terminology_translator
        
        for doc_type in DocumentType:
            collection_name = self._get_collection_name(doc_type)
            try:
                collection = self.client.get_collection(collection_name)
                all_docs = collection.get(include=["documents", "metadatas"])
                for i, doc in enumerate(all_docs["documents"]):
                    if card_no_upper in doc[:300]:
                        content = doc
                        if translate_result:
                            content = terminology_translator.translate_result_to_chinese(content)
                        
                        results.append({
                            "content": content,
                            "content_original": doc,
                            "metadata": all_docs["metadatas"][i],
                            "score": 0.0,
                            "doc_type": doc_type.value
                        })
                        print(f"[卡牌搜索] 从向量库找到: {card_no_upper}")
                        break
            except Exception as e:
                print(f"[卡牌搜索] 向量库搜索错误: {e}")
                continue
        
        print(f"[卡牌搜索] {card_no_upper} 共找到 {len(results)} 条结果")
        return results[:3]
    
    def delete_document(self, doc_id: str, doc_type: DocumentType) -> bool:
        """删除指定文档"""
        collection_name = self._get_collection_name(doc_type)
        try:
            collection = self.client.get_collection(collection_name)
            # 查找所有属于该文档的 chunks
            results = collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                collection.delete(ids=results["ids"])
                return True
        except Exception:
            pass
        return False
    
    def list_documents(self, doc_type: Optional[DocumentType] = None) -> List[dict]:
        """列出所有文档"""
        doc_types = [doc_type] if doc_type else list(DocumentType)
        documents = {}
        
        for dt in doc_types:
            collection_name = self._get_collection_name(dt)
            try:
                collection = self.client.get_collection(collection_name)
                results = collection.get()
                for meta in results["metadatas"]:
                    doc_id = meta.get("doc_id")
                    if doc_id and doc_id not in documents:
                        documents[doc_id] = {
                            "doc_id": doc_id,
                            "title": meta.get("title", ""),
                            "doc_type": meta.get("doc_type", ""),
                            "created_at": meta.get("created_at", ""),
                            "tags": meta.get("tags", ""),
                            "chunk_count": 0
                        }
                    if doc_id:
                        documents[doc_id]["chunk_count"] += 1
            except Exception:
                continue
        
        return list(documents.values())
    
    def get_document_chunks(self, doc_id: str) -> List[dict]:
        """获取文档的所有分块"""
        chunks = []
        for doc_type in DocumentType:
            collection_name = self._get_collection_name(doc_type)
            try:
                collection = self.client.get_collection(collection_name)
                results = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
                for i, (doc_content, meta) in enumerate(zip(results["documents"], results["metadatas"])):
                    chunks.append({
                        "chunk_index": meta.get("chunk_index", i),
                        "content": doc_content,
                        "metadata": meta
                    })
            except Exception:
                continue
        
        # 按 chunk_index 排序
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks


# 单例
vector_store = VectorStoreManager()
