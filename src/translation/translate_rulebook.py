"""
DTCG Rulebook Translator
Translates Japanese rulebook to Chinese while maintaining terminology consistency
with the existing Chinese rulebook.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class RulebookTranslator:
    def __init__(self, chinese_ref_path: str, japanese_path: str):
        self.chinese_ref_path = chinese_ref_path
        self.japanese_path = japanese_path
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.terminology_dict = {}
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def build_terminology_dict(self, chinese_text: str) -> Dict[str, str]:
        """
        Extract terminology from Chinese reference rulebook.
        Uses LLM to identify key game terms and their Chinese translations.
        """
        print("Building terminology dictionary from Chinese reference...")
        
        prompt = f"""从以下中文游戏规则书中提取专有名词术语对照表。
请识别游戏中的关键术语，包括但不限于：
- 卡牌类型（如：数码蛋、数码兽、驯兽师等）
- 游戏区域（如：育成区、战斗区、手牌等）
- 游戏动作（如：进化、孵化、攻击等）
- 卡牌属性和状态
- 游戏阶段和回合

以JSON格式返回，格式为 {{"日文术语": "中文术语"}}

中文规则书内容（前3000字）：
{chinese_text[:3000]}
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的游戏术语提取专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the response to extract terminology
        result = response.choices[0].message.content
        print(f"Extracted terminology preview:\n{result[:500]}...\n")
        
        return result
    
    def translate_chunk(self, japanese_text: str, terminology_ref: str, chunk_num: int, total_chunks: int) -> str:
        """
        Translate a chunk of Japanese text to Chinese using terminology reference.
        """
        print(f"Translating chunk {chunk_num}/{total_chunks}...")
        
        prompt = f"""请将以下日文游戏规则翻译成中文。

重要要求：
1. 必须使用提供的术语对照表中的中文术语
2. 保持专业、准确的翻译风格
3. 保留原文的格式和结构
4. 数字、符号保持不变
5. 确保游戏规则的逻辑清晰

术语对照表参考：
{terminology_ref}

待翻译的日文内容：
{japanese_text}

请直接输出翻译后的中文内容，不要添加额外说明。
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的日中游戏规则翻译专家，精通DTCG卡牌游戏。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def split_text_into_chunks(self, text: str, max_chars: int = 2000) -> List[str]:
        """Split text into manageable chunks for translation"""
        # Try to split by paragraphs or sections
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def translate_rulebook(self, output_path: str):
        """Main translation workflow"""
        print("=" * 60)
        print("DTCG Rulebook Translation Tool")
        print("=" * 60)
        
        # Step 1: Extract text from both PDFs
        print("\n[1/4] Extracting text from Chinese reference rulebook...")
        chinese_text = self.extract_pdf_text(self.chinese_ref_path)
        print(f"Extracted {len(chinese_text)} characters from Chinese rulebook")
        
        print("\n[2/4] Extracting text from Japanese rulebook...")
        japanese_text = self.extract_pdf_text(self.japanese_path)
        print(f"Extracted {len(japanese_text)} characters from Japanese rulebook")
        
        # Step 2: Build terminology dictionary
        print("\n[3/4] Building terminology dictionary...")
        terminology_ref = self.build_terminology_dict(chinese_text)
        
        # Step 3: Translate Japanese text in chunks
        print("\n[4/4] Translating Japanese rulebook...")
        chunks = self.split_text_into_chunks(japanese_text)
        print(f"Split into {len(chunks)} chunks for translation")
        
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            translated = self.translate_chunk(chunk, terminology_ref, i, len(chunks))
            translated_chunks.append(translated)
        
        # Combine all translated chunks
        final_translation = "\n\n".join(translated_chunks)
        
        # Step 4: Save the result
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_translation)
        
        print(f"\n{'=' * 60}")
        print(f"Translation completed!")
        print(f"Output saved to: {output_path}")
        print(f"Total characters translated: {len(final_translation)}")
        print(f"{'=' * 60}")


def main():
    # File paths
    chinese_ref = "数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf"
    japanese_new = "general_rule.pdf"
    output_file = "数码宝贝卡牌对战_综合规则_最新版_中文翻译.txt"
    
    # Create translator and run
    translator = RulebookTranslator(chinese_ref, japanese_new)
    translator.translate_rulebook(output_file)


if __name__ == "__main__":
    main()
