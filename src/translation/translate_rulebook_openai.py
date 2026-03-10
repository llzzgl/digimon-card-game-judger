"""
DTCG Rulebook Translator (OpenAI Version - Optimized)
使用 OpenAI API 进行翻译，支持代理配置
"""

import os
from typing import List
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
import json
import httpx

load_dotenv()

# 配置代理
proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
proxy_port = os.getenv("PROXY_PORT", "7890")
proxy_url = f"http://{proxy_host}:{proxy_port}"
use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"

if use_proxy:
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    print(f"✅ 已启用代理: {proxy_url}")


class RulebookTranslatorOpenAI:
    def __init__(self, chinese_ref_path: str, japanese_path: str):
        self.chinese_ref_path = chinese_ref_path
        self.japanese_path = japanese_path
        
        # 支持自定义 base_url 和代理
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")  # 可选：自定义 API 端点
        
        # 配置 HTTP 客户端（支持代理）
        http_client = None
        if use_proxy:
            http_client = httpx.Client(proxy=proxy_url)
        
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        else:
            self.client = OpenAI(api_key=api_key, http_client=http_client)
        
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
        print("正在从中文规则书提取术语...")
        
        prompt = f"""从以下中文游戏规则书中提取专有名词术语。
请识别游戏中的关键术语，包括：
- 卡牌类型（如：数码蛋、数码兽、驯兽师、选项卡）
- 游戏区域（如：育成区、战斗区、安全区、废弃区、手牌、卡组）
- 游戏动作（如：进化、孵化、攻击、休眠、激活、抽牌）
- 卡牌属性（如：进化费用、DP、进化源）
- 游戏阶段（如：抽牌阶段、育成阶段、主要阶段）

以简洁的列表形式返回，每行一个术语。

中文规则书内容（前4000字）：
{chinese_text[:4000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # 使用更快更便宜的模型提取术语
                messages=[
                    {"role": "system", "content": "你是一个专业的游戏术语提取专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            print(f"提取的术语示例:\n{result[:300]}...\n")
            return result
            
        except Exception as e:
            print(f"术语提取失败: {e}")
            # 返回基础术语列表作为后备
            return """
基础术语：
数码蛋、数码兽、驯兽师、选项卡
育成区、战斗区、安全区、废弃区、手牌、卡组
进化、孵化、攻击、休眠、激活
进化费用、DP（数码力量）、进化源
抽牌阶段、育成阶段、主要阶段
            """
    
    def translate_chunk(self, japanese_text: str, terminology_ref: str, chunk_num: int, total_chunks: int) -> str:
        """Translate a chunk of Japanese text to Chinese"""
        print(f"正在翻译第 {chunk_num}/{total_chunks} 块...")
        
        prompt = f"""请将以下日文游戏规则翻译成中文。

重要要求：
1. 使用提供的术语对照表中的中文术语
2. 保持专业、准确的翻译风格
3. 保留原文的格式和结构
4. 数字、符号保持不变
5. 确保游戏规则的逻辑清晰

术语参考：
{terminology_ref}

待翻译的日文内容：
{japanese_text}

请直接输出翻译后的中文内容。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 使用性价比高的模型
                messages=[
                    {"role": "system", "content": "你是专业的日中游戏规则翻译专家，精通DTCG卡牌游戏。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"翻译第 {chunk_num} 块时出错: {e}")
            return f"[翻译失败 - Chunk {chunk_num}]\n{japanese_text}"
    
    def split_text_into_chunks(self, text: str, max_chars: int = 2500) -> List[str]:
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
        print("DTCG 规则书翻译工具 (OpenAI)")
        print("=" * 60)
        
        print("\n[1/4] 提取中文参考规则书...")
        chinese_text = self.extract_pdf_text(self.chinese_ref_path)
        print(f"已提取 {len(chinese_text)} 字符")
        
        print("\n[2/4] 提取日文规则书...")
        japanese_text = self.extract_pdf_text(self.japanese_path)
        print(f"已提取 {len(japanese_text)} 字符")
        
        print("\n[3/4] 构建术语对照表...")
        terminology_ref = self.build_terminology_dict(chinese_text)
        
        print("\n[4/4] 开始翻译...")
        chunks = self.split_text_into_chunks(japanese_text)
        print(f"分为 {len(chunks)} 块进行翻译\n")
        
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            translated = self.translate_chunk(chunk, terminology_ref, i, len(chunks))
            translated_chunks.append(translated)
        
        final_translation = "\n\n".join(translated_chunks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_translation)
        
        print(f"\n{'=' * 60}")
        print(f"✅ 翻译完成！")
        print(f"输出文件: {output_path}")
        print(f"翻译字符数: {len(final_translation)}")
        print(f"{'=' * 60}")


def main():
    chinese_ref = "数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf"
    japanese_new = "general_rule.pdf"
    output_file = "数码宝贝卡牌对战_综合规则_最新版_中文翻译.txt"
    
    translator = RulebookTranslatorOpenAI(chinese_ref, japanese_new)
    translator.translate_rulebook(output_file)


if __name__ == "__main__":
    main()
