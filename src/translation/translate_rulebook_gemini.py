"""
DTCG Rulebook Translator (Gemini Version)
Uses Google Gemini API for translation - more cost-effective alternative
"""

import os
from typing import Dict, List
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# 配置代理
proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
proxy_port = os.getenv("PROXY_PORT", "7897")
proxy_url = f"http://{proxy_host}:{proxy_port}"

if os.getenv("USE_PROXY", "false").lower() == "true":
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    os.environ["GRPC_PROXY"] = proxy_url
    print(f"✅ 已启用代理: {proxy_url}")


class RulebookTranslatorGemini:
    def __init__(self, chinese_ref_path: str, japanese_path: str):
        self.chinese_ref_path = chinese_ref_path
        self.japanese_path = japanese_path
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # 使用最新模型
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def build_terminology_dict(self, chinese_text: str) -> str:
        """Extract terminology from Chinese reference rulebook"""
        print("Building terminology dictionary from Chinese reference...")
        
        prompt = f"""从以下中文游戏规则书中提取专有名词术语对照表。
请识别游戏中的关键术语，包括但不限于：
- 卡牌类型（如：数码蛋、数码兽、驯兽师等）
- 游戏区域（如：育成区、战斗区、手牌等）
- 游戏动作（如：进化、孵化、攻击等）
- 卡牌属性和状态
- 游戏阶段和回合

请列出主要术语及其对应的日文（如果能推断）。

中文规则书内容（前3000字）：
{chinese_text[:3000]}
"""
        
        response = self.model.generate_content(prompt)
        result = response.text
        print(f"Extracted terminology preview:\n{result[:500]}...\n")
        
        return result
    
    def translate_chunk(self, japanese_text: str, terminology_ref: str, chunk_num: int, total_chunks: int) -> str:
        """Translate a chunk of Japanese text to Chinese"""
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
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def split_text_into_chunks(self, text: str, max_chars: int = 3000) -> List[str]:
        """Split text into manageable chunks"""
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
        print("DTCG Rulebook Translation Tool (Gemini)")
        print("=" * 60)
        
        print("\n[1/4] Extracting text from Chinese reference rulebook...")
        chinese_text = self.extract_pdf_text(self.chinese_ref_path)
        print(f"Extracted {len(chinese_text)} characters from Chinese rulebook")
        
        print("\n[2/4] Extracting text from Japanese rulebook...")
        japanese_text = self.extract_pdf_text(self.japanese_path)
        print(f"Extracted {len(japanese_text)} characters from Japanese rulebook")
        
        print("\n[3/4] Building terminology dictionary...")
        terminology_ref = self.build_terminology_dict(chinese_text)
        
        print("\n[4/4] Translating Japanese rulebook...")
        chunks = self.split_text_into_chunks(japanese_text)
        print(f"Split into {len(chunks)} chunks for translation")
        
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            try:
                translated = self.translate_chunk(chunk, terminology_ref, i, len(chunks))
                translated_chunks.append(translated)
            except Exception as e:
                print(f"Error translating chunk {i}: {e}")
                translated_chunks.append(f"[翻译失败 - Chunk {i}]\n{chunk}")
        
        final_translation = "\n\n".join(translated_chunks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_translation)
        
        print(f"\n{'=' * 60}")
        print(f"Translation completed!")
        print(f"Output saved to: {output_path}")
        print(f"Total characters translated: {len(final_translation)}")
        print(f"{'=' * 60}")


def main():
    chinese_ref = "数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf"
    japanese_new = "general_rule.pdf"
    output_file = "数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt"
    
    translator = RulebookTranslatorGemini(chinese_ref, japanese_new)
    translator.translate_rulebook(output_file)


if __name__ == "__main__":
    main()
