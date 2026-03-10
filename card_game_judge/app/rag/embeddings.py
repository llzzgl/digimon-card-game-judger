"""
嵌入提供商抽象层

支持多种嵌入模型：
- OpenAI
- Google Gemini
- 本地模型 (HuggingFace)
- Ollama
"""
import os
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np


class EmbeddingProvider(ABC):
    """嵌入提供商基类"""
    
    def __init__(self, model: str, max_input_tokens: Optional[int] = None):
        self.model = model
        self.max_input_tokens = max_input_tokens
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """生成单个查询的嵌入"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入"""
        pass
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """归一化嵌入向量"""
        arr = np.array(embedding)
        magnitude = np.linalg.norm(arr)
        if magnitude < 1e-10:
            return embedding
        return (arr / magnitude).tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI 嵌入提供商"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        super().__init__(model, max_input_tokens=8191)
        from langchain_openai import OpenAIEmbeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model=model
        )
    
    def embed_query(self, text: str) -> List[float]:
        return self.normalize_embedding(self.embeddings.embed_query(text))
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.embeddings.embed_documents(texts)
        return [self.normalize_embedding(emb) for emb in embeddings]


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini 嵌入提供商"""
    
    def __init__(self, api_key: str, model: str = "models/text-embedding-004"):
        super().__init__(model, max_input_tokens=2048)
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
    
    def embed_query(self, text: str) -> List[float]:
        import google.generativeai as genai
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_query"
        )
        return self.normalize_embedding(result['embedding'])
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        import google.generativeai as genai
        result = genai.embed_content(
            model=self.model_name,
            content=texts,
            task_type="retrieval_document"
        )
        return [self.normalize_embedding(emb) for emb in result['embedding']]


class LocalEmbeddingProvider(EmbeddingProvider):
    """本地 HuggingFace 嵌入提供商"""
    
    def __init__(self, model: str = "BAAI/bge-m3", device: str = "cpu"):
        super().__init__(model, max_input_tokens=8192)
        from langchain_community.embeddings import HuggingFaceEmbeddings
        import os
        
        try:
            print(f"正在加载嵌入模型: {model}")
            print("提示: 首次运行会下载模型（约 2.27GB），请耐心等待...")
            
            # 设置离线模式，避免检查更新
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True},
                # 添加缓存目录，确保使用本地缓存
                cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
            )
            
            print("✅ 模型加载成功")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ 模型加载失败: {error_msg}\n")
            
            # 如果是网络错误，尝试完全离线模式
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "10061" in error_msg:
                print("检测到网络错误，尝试完全离线模式...")
                try:
                    # 完全离线模式
                    os.environ['TRANSFORMERS_OFFLINE'] = '1'
                    os.environ['HF_HUB_OFFLINE'] = '1'
                    os.environ['HF_DATASETS_OFFLINE'] = '1'
                    
                    # 使用本地缓存
                    from sentence_transformers import SentenceTransformer
                    
                    # 直接加载本地模型
                    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                    model_path = os.path.join(cache_dir, f"models--{model.replace('/', '--')}")
                    
                    if os.path.exists(model_path):
                        print(f"使用本地缓存: {model_path}")
                        # 找到实际的模型目录
                        snapshots_dir = os.path.join(model_path, "snapshots")
                        if os.path.exists(snapshots_dir):
                            snapshot_dirs = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
                            if snapshot_dirs:
                                actual_model_path = os.path.join(snapshots_dir, snapshot_dirs[0])
                                print(f"加载模型: {actual_model_path}")
                                
                                # 使用 sentence_transformers 直接加载
                                st_model = SentenceTransformer(actual_model_path, device=device)
                                
                                # 包装为 LangChain 兼容的接口
                                class OfflineEmbeddings:
                                    def __init__(self, model):
                                        self.model = model
                                    
                                    def embed_query(self, text):
                                        return self.model.encode(text, normalize_embeddings=True).tolist()
                                    
                                    def embed_documents(self, texts):
                                        return self.model.encode(texts, normalize_embeddings=True).tolist()
                                
                                self.embeddings = OfflineEmbeddings(st_model)
                                print("✅ 离线模式加载成功")
                                return
                    
                    raise Exception("本地缓存不存在或不完整")
                    
                except Exception as offline_error:
                    print(f"离线模式也失败: {offline_error}")
            
            # 提供详细的错误提示
            print("=" * 60)
            print("模型加载失败 - 可能的解决方案:")
            print("=" * 60)
            print("1. 确保模型已下载:")
            print("   运行: python check_network.py")
            print()
            print("2. 设置环境变量（在运行前）:")
            print("   set HF_ENDPOINT=https://hf-mirror.com")
            print("   set TRANSFORMERS_OFFLINE=1")
            print()
            print("3. 或使用 API 服务代替本地模型:")
            print("   - OpenAI: create_embedding_provider('openai', api_key='...')")
            print("   - Gemini: create_embedding_provider('gemini', api_key='...')")
            print("=" * 60)
            
            raise RuntimeError(
                f"无法加载嵌入模型。请检查网络连接或使用 API 服务。\n"
                f"详细错误: {error_msg}"
            )
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama 本地嵌入提供商"""
    
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        super().__init__(model)
        from langchain_community.embeddings import OllamaEmbeddings
        self.embeddings = OllamaEmbeddings(
            model=model,
            base_url=base_url
        )
    
    def embed_query(self, text: str) -> List[float]:
        return self.normalize_embedding(self.embeddings.embed_query(text))
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.embeddings.embed_documents(texts)
        return [self.normalize_embedding(emb) for emb in embeddings]


def create_embedding_provider(
    provider: str = "local",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """
    创建嵌入提供商
    
    Args:
        provider: 提供商类型 ("openai", "gemini", "local", "ollama")
        model: 模型名称
        api_key: API 密钥（如需要）
        **kwargs: 其他参数
    
    Returns:
        EmbeddingProvider 实例
    """
    provider = provider.lower()
    
    if provider == "openai":
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        model = model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(api_key, model)
    
    elif provider == "gemini":
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required")
        model = model or "models/text-embedding-004"
        return GeminiEmbeddingProvider(api_key, model)
    
    elif provider == "ollama":
        model = model or "nomic-embed-text"
        base_url = kwargs.get("base_url", "http://localhost:11434")
        return OllamaEmbeddingProvider(model, base_url)
    
    elif provider == "local":
        model = model or "BAAI/bge-m3"
        device = kwargs.get("device", "cpu")
        return LocalEmbeddingProvider(model, device)
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
