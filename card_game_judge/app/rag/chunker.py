"""
文档分块器

支持多种分块策略：
- 按章节分块 (适用于规则文档)
- 按 QA 条目分块 (适用于裁定数据)
- 整卡分块 (适用于卡牌数据，不分割)
- 递归字符分块 (通用后备策略)
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
        if doc_type == DocumentType.RULE:
            # 规则：按章节分块
            return self._chunk_by_section(text)
        elif doc_type == DocumentType.RULING:
            # 裁定：按 QA 条目分块
            return self._chunk_qa(text)
        elif doc_type == DocumentType.CARD:
            # 卡牌：整卡分块（不分割）
            return self._chunk_card(text)
        else:
            # 默认：递归字符分块
            return self._chunk_recursive(text)
    
    def _chunk_by_section(self, text: str) -> List[str]:
        """
        按章节分块（适用于规则文档）
        
        策略：
        1. 识别章节标题（如"第 8 章"、"8.1"、"Section 1"等）
        2. 每个章节作为一个独立块
        3. 如果章节过长，递归分割
        """
        # 章节标题模式
        section_patterns = [
            r'(第 [零一二三四五六七八九十百\d]+章 [^\n]*)',  # 第 X 章 XXX
            r'^(\d+\.\d+[^\n]*)',  # 8.1 XXX
            r'^(Chapter\s+\d+[^\n]*)',  # Chapter X
            r'^(Section\s+\d+[^\n]*)',  # Section X
            r'^([八七八九十百]+\、[^\n]*)',  # 一、XXX
        ]
        
        chunks = []
        current_section = ""
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            is_section_header = False
            
            for pattern in section_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    # 保存之前的章节
                    if current_section and current_content:
                        section_text = f"{current_section}\n" + "\n".join(current_content)
                        if len(section_text) > self.config.chunk_size:
                            # 章节过长，递归分割
                            chunks.extend(self._chunk_recursive(section_text))
                        else:
                            chunks.append(section_text)
                    
                    # 开始新章节
                    current_section = line.strip()
                    current_content = []
                    is_section_header = True
                    break
            
            if not is_section_header and line.strip():
                current_content.append(line)
        
        # 添加最后一个章节
        if current_section and current_content:
            section_text = f"{current_section}\n" + "\n".join(current_content)
            if len(section_text) > self.config.chunk_size:
                chunks.extend(self._chunk_recursive(section_text))
            else:
                chunks.append(section_text)
        
        # 如果没有识别到章节，使用递归分块
        if not chunks:
            chunks = self._chunk_recursive(text)
        
        return chunks
    
    def _chunk_recursive(self, text: str) -> List[str]:
        """
        递归字符分块（通用后备策略）
        
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
        QA 数据分块（适用于裁定）
        
        策略：
        - 每个 QA 对作为一个独立块
        - 如果单个 QA 过长，按段落分割
        """
        # 尝试识别 QA 格式
        qa_patterns = [
            r'Q[:\s：](.+?)A[:\s：](.+?)(?=Q[:\s：]|$)',  # Q: ... A: ...
            r'问 [:\s：](.+?) 答 [:\s：](.+?)(?=问 [:\s：]|$)',  # 问：... 答：...
            r'【问题】(.+?)【回答】(.+?)(?=【问题】|$)',  # 【问题】...【回答】...
            r'【Q】(.+?)【A】(.+?)(?=【Q】|$)',  # 【Q】...【A】...
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
        - 卡牌数据通常较短，整体作为一个块（不分割）
        - 保持卡牌完整性，便于检索
        - 只有当超过最大限制时才分割
        """
        # 卡牌数据应该保持完整，不分割
        # 除非超过配置的最大 chunk_size
        if len(text) <= self.config.chunk_size:
            return [text]
        
        # 如果卡牌数据过长（罕见情况），尝试按字段分割
        # 但优先保持关键字段完整
        field_patterns = [
            r'(卡牌编号 [:\s：][^\n]+)',
            r'(中文名 [:\s：][^\n]+)',
            r'(日文名 [:\s：][^\n]+)',
            r'(类型 [:\s：][^\n]+)',
            r'(效果 [:\s：][^\n]+)',
            r'(进化条件 [:\s：][^\n]+)',
            r'(继承效果 [:\s：][^\n]+)',
            r'(安防效果 [:\s：][^\n]+)',
        ]
        
        chunks = []
        current_chunk = ""
        
        # 尝试按字段分割
        for pattern in field_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                field_text = match.group(0)
                
                if len(current_chunk) + len(field_text) <= self.config.chunk_size:
                    current_chunk += field_text + "\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = field_text + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 如果仍然无法分割，强制按长度分割
        return chunks if chunks else self._split_by_length(text)
    
    def estimate_chunks(self, text: str) -> int:
        """估算文本会被分成多少块"""
        if not text:
            return 0
        return max(1, len(text) // self.config.chunk_size)
