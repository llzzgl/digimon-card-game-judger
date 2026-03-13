"""
PDF 解析工具
PDF Parser Utilities
"""
from pathlib import Path
from typing import List, Optional
import re


class PDFParser:
    """PDF 解析器"""
    
    def __init__(self):
        self.reader = None
    
    def extract_text(self, pdf_path: str) -> str:
        """
        从 PDF 提取文本
        
        Args:
            pdf_path: PDF 文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("请安装 pypdf: pip install pypdf")
        
        text = ""
        with open(pdf_path, 'rb') as file:
            self.reader = PdfReader(file)
            for page in self.reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
    
    def extract_text_by_pages(self, pdf_path: str, 
                              start_page: Optional[int] = None,
                              end_page: Optional[int] = None) -> List[str]:
        """
        按页面提取文本
        
        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码（0-indexed）
            end_page: 结束页码（0-indexed，包含）
        
        Returns:
            每页文本的列表
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("请安装 pypdf: pip install pypdf")
        
        pages_text = []
        
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            
            # 确定页面范围
            total_pages = len(reader.pages)
            start = start_page if start_page is not None else 0
            end = end_page if end_page is not None else total_pages - 1
            
            # 验证范围
            start = max(0, min(start, total_pages - 1))
            end = max(start, min(end, total_pages - 1))
            
            for i in range(start, end + 1):
                page_text = reader.pages[i].extract_text()
                pages_text.append(page_text if page_text else "")
        
        return pages_text
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        获取 PDF 页数
        
        Args:
            pdf_path: PDF 文件路径
        
        Returns:
            页数
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("请安装 pypdf: pip install pypdf")
        
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            return len(reader.pages)
    
    def split_text_into_chunks(self, text: str, max_chars: int = 2500) -> List[str]:
        """
        将文本分割成适合翻译的块
        
        Args:
            text: 待分割的文本
            max_chars: 每块最大字符数
        
        Returns:
            文本块列表
        """
        # 尝试按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果单个段落超过最大长度，进一步分割
                if len(para) > max_chars:
                    sub_chunks = self._split_long_paragraph(para, max_chars)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"
        
        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> List[str]:
        """
        分割过长的段落
        
        Args:
            paragraph: 过长的段落
            max_chars: 每块最大字符数
        
        Returns:
            分割后的文本块列表
        """
        chunks = []
        
        # 尝试按句子分割
        sentences = re.split(r'([。！？.!?])', paragraph)
        
        current_chunk = ""
        for sentence in sentences:
            if not sentence:
                continue
            
            # 添加标点符号回句子
            if sentence in '。！？.!?':
                current_chunk += sentence
                if len(current_chunk) >= max_chars * 0.8:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
            else:
                if len(current_chunk) + len(sentence) < max_chars:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 如果仍然无法分割，强制按字符分割
        if not chunks and len(paragraph) > max_chars:
            for i in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[i:i + max_chars])
        
        return chunks


def extract_pdf_text(pdf_path: str) -> str:
    """
    便捷函数：从 PDF 提取文本
    
    Args:
        pdf_path: PDF 文件路径
    
    Returns:
        提取的文本内容
    """
    parser = PDFParser()
    return parser.extract_text(pdf_path)
