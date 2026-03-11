"""
文档分块器

支持多种分块策略：
- 递归字符分块 (适用于规则文档)
- 语义分块 (适用于 QA 数据)
- 固定大小分块 (通用)
"""
from typing import List, Optional
import re

from .types import ChunkConfig, DocumentType


class DocumentChunker:
    """文档分块器"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        初始化分块器
        
        Args:
            config: 分块配置
        """
        self.config = config or ChunkConfig()
    
    def chunk_text(
        self,
        text: str,
        doc_type: Optional[DocumentType] = None
    ) -> List[str]:
        """
        对文本进行分块
        
        Args:
            text: 输入文本
            doc_type: 文档类型 (用于选择分块策略)
        
        Returns:
            分块后的文本列表
        """
        if not text or not text.strip():
            return []
        
        # 根据文档类型选择分块策略
        if doc_type == DocumentType.RULING:
            return self._chunk_qa(text)
        elif doc_type == DocumentType.CARD:
            return self._chunk_card(text)
        else:
            return self._chunk_recursive(text)
    
    def _chunk_recursive(self, text: str) -> List[str]:
        """
        递归字符分块 (适用于规则文档)
        
        策略：
        1. 优先按段落分割 (\n\n)
        2. 其次按句子分割 (。；)
        3. 最后按字符分割
        """
        separators = ["\n\n", "\n", "。", "；", ".", ";", " ", ""]
        return self._split_text_recursive(text, separators)
    
    def _split_text_recursive(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """递归分割文本"""
        if not separators:
            # 最后一级：按字符强制分割
            return self._split_by_length(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if not separator:
            # 空分隔符：按字符分割
            return self._split_by_length(text)
        
        # 按当前分隔符分割
        splits = text.split(separator)
        
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # 如果当前块 + 新片段不超过限制，合并
            test_chunk = current_chunk + separator + split if current_chunk else split
            
            if len(test_chunk) <= self.config.chunk_size:
                current_chunk = test_chunk
            else:
                # 当前块已满
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个片段超过限制，递归分割
                if len(split) > self.config.chunk_size:
                    chunks.extend(
                        self._split_text_recursive(split, remaining_separators)
                    )
                    current_chunk = ""
                else:
                    current_chunk = split
        
        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk)
        
        # 添加重叠
        if self.config.chunk_overlap > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_by_length(self, text: str) -> List[str]:
        """按固定长度分割"""
        chunks = []
        for i in range(0, len(text), self.config.chunk_size):
            chunks.append(text[i:i + self.config.chunk_size])
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """添加块之间的重叠"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]
            
            # 从前一块取后 overlap 个字符
            overlap_text = prev_chunk[-self.config.chunk_overlap:]
            
            # 添加到当前块前面
            overlapped.append(overlap_text + curr_chunk)
        
        return overlapped
    
    def _chunk_qa(self, text: str) -> List[str]:
        """
        QA 数据分块 (适用于裁定)
        
        策略：
        - 每个 QA 对作为一个独立块
        - 如果单个 QA 过长，按段落分割
        """
        # 尝试识别 QA 格式
        qa_patterns = [
            r'Q[:\s：](.+?)A[:\s：](.+?)(?=Q[:\s：]|$)',  # Q: ... A: ...
            r'问[:\s：](.+?)答[:\s：](.+?)(?=问[:\s：]|$)',  # 问: ... 答: ...
            r'【问题】(.+?)【回答】(.+?)(?=【问题】|$)',  # 【问题】...【回答】...
        ]
        
        for pattern in qa_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            qa_pairs = []
            for match in matches:
                q = match.group(1).strip()
                a = match.group(2).strip()
                qa_text = f"Q: {q}\nA: {a}"
                
                # 如果单个 QA 过长，分割
                if len(qa_text) > self.config.chunk_size:
                    qa_pairs.extend(self._chunk_recursive(qa_text))
                else:
                    qa_pairs.append(qa_text)
            
            if qa_pairs:
                return qa_pairs
        
        # 如果没有识别到 QA 格式，使用递归分块
        return self._chunk_recursive(text)
    
    def _chunk_card(self, text: str) -> List[str]:
        """
        卡牌数据分块
        
        策略：
        - 卡牌数据通常较短，整体作为一个块
        - 如果过长，按字段分割
        """
        if len(text) <= self.config.chunk_size:
            return [text]
        
        # 尝试按字段分割
        field_pattern = r'(卡牌编号|中文名|日文名|类型|效果|进化条件|继承效果|安防效果)[:\s：]'
        fields = re.split(field_pattern, text)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(fields), 2):
            if i + 1 < len(fields):
                field_text = fields[i] + fields[i + 1]
            else:
                field_text = fields[i]
            
            if len(current_chunk) + len(field_text) <= self.config.chunk_size:
                current_chunk += field_text
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = field_text
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def estimate_chunks(self, text: str) -> int:
        """估算文本会被分成多少块"""
        if not text:
            return 0
        return max(1, len(text) // self.config.chunk_size)
