"""
规则书翻译任务
Rulebook Translation Task
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import time

from ..translator import Translator, TranslationEngine
from ..utils.terminology import TerminologyManager, load_terminology_from_project
from ..utils.pdf_parser import PDFParser
from ..config.translation_config import TranslationConfig


class RulebookTranslator:
    """规则书翻译器"""
    
    def __init__(self, 
                 chinese_ref_path: Optional[str] = None,
                 japanese_path: Optional[str] = None,
                 engine_type: str = "openai"):
        """
        初始化规则书翻译器
        
        Args:
            chinese_ref_path: 中文参考规则书 PDF 路径
            japanese_path: 日文规则书 PDF 路径
            engine_type: 使用的翻译引擎 ('openai', 'gemini', 'qwen')
        """
        self.chinese_ref_path = Path(chinese_ref_path) if chinese_ref_path else None
        self.japanese_path = Path(japanese_path) if japanese_path else None
        self.engine_type = engine_type
        
        # 初始化组件
        self.translator = Translator(default_engine=engine_type)
        self.terminology_manager = TerminologyManager()
        self.pdf_parser = PDFParser()
        
        # 翻译状态
        self.chinese_text = ""
        self.japanese_text = ""
        self.terminology_ref = ""
    
    def extract_texts(self) -> Dict[str, int]:
        """
        从 PDF 提取文本
        
        Returns:
            提取的字符数统计
        """
        stats = {}
        
        # 提取中文参考文本
        if self.chinese_ref_path and self.chinese_ref_path.exists():
            print(f"\n[1/4] 提取中文参考规则书：{self.chinese_ref_path.name}")
            self.chinese_text = self.pdf_parser.extract_text(str(self.chinese_ref_path))
            stats['chinese_chars'] = len(self.chinese_text)
            print(f"✓ 已提取 {stats['chinese_chars']} 字符")
        else:
            print("⚠ 未提供中文参考规则书路径")
            self.chinese_text = ""
            stats['chinese_chars'] = 0
        
        # 提取日文规则书文本
        if self.japanese_path and self.japanese_path.exists():
            print(f"\n[2/4] 提取日文规则书：{self.japanese_path.name}")
            self.japanese_text = self.pdf_parser.extract_text(str(self.japanese_path))
            stats['japanese_chars'] = len(self.japanese_text)
            print(f"✓ 已提取 {stats['japanese_chars']} 字符")
        else:
            raise FileNotFoundError(f"日文规则书不存在：{self.japanese_path}")
        
        return stats
    
    def build_terminology(self) -> str:
        """
        从中文参考构建术语表
        
        Returns:
            术语参考文本
        """
        print("\n[3/4] 构建术语对照表...")
        
        # 加载项目术语表
        project_root = TranslationConfig.PROJECT_ROOT
        self.terminology_manager = load_terminology_from_project(project_root)
        
        # 如果有中文参考文本，使用 LLM 提取额外术语
        if self.chinese_text:
            engine = self.translator.get_engine(self.engine_type)
            if engine:
                try:
                    prompt = f"""从以下中文游戏规则书中提取专有名词术语列表。
请识别游戏中的关键术语，包括：
- 卡牌类型（如：数码蛋、数码兽、驯兽师、选项卡）
- 游戏区域（如：育成区、战斗区、安全区、废弃区、手牌、卡组）
- 游戏动作（如：进化、孵化、攻击、休眠、激活、抽牌）
- 卡牌属性（如：进化费用、DP、进化源）
- 游戏阶段（如：抽牌阶段、育成阶段、主要阶段）

以简洁的列表形式返回，每行一个术语，不要解释。

中文规则书内容（前 4000 字）：
{self.chinese_text[:4000]}
"""
                    print("  正在使用 LLM 提取额外术语...")
                    extracted_terms = engine.translate_text(prompt)
                    print(f"✓ 提取到额外术语:\n{extracted_terms[:300]}...")
                except Exception as e:
                    print(f"⚠ LLM 术语提取失败：{e}")
                    extracted_terms = ""
            else:
                extracted_terms = ""
        else:
            extracted_terms = ""
        
        # 构建术语参考文本
        term_list = self.terminology_manager.terminology
        terms_text = "\n".join([f"  {jp} → {cn}" for jp, cn in list(term_list.items())[:100]])
        
        if len(term_list) > 100:
            terms_text += f"\n  ... (共{len(term_list)}个术语)"
        
        if extracted_terms:
            self.terminology_ref = f"基础术语表:\n{terms_text}\n\n额外提取术语:\n{extracted_terms}"
        else:
            self.terminology_ref = f"基础术语表:\n{terms_text}"
        
        print(f"\n✓ 术语表构建完成（共{len(term_list)}个术语）")
        
        return self.terminology_ref
    
    def translate_chunk(self, japanese_text: str, chunk_num: int, 
                       total_chunks: int) -> str:
        """
        翻译单个文本块
        
        Args:
            japanese_text: 日文文本块
            chunk_num: 当前块编号
            total_chunks: 总块数
        
        Returns:
            翻译后的中文文本
        """
        print(f" [{chunk_num}/{total_chunks}]", end='', flush=True)
        
        # 准备上下文
        context = {
            "terminology": self.terminology_manager.terminology
        }
        
        # 翻译
        try:
            translated = self.translator.translate(
                japanese_text, 
                engine=self.engine_type,
                context=context
            )
            return translated
        except Exception as e:
            print(f" [错误：{e}]", end='', flush=True)
            return f"[翻译失败 - Chunk {chunk_num}]\n{japanese_text}"
    
    def translate_rulebook(self, output_path: Optional[str] = None) -> Dict:
        """
        主翻译流程
        
        Args:
            output_path: 输出文件路径（可选，默认使用配置路径）
        
        Returns:
            翻译统计信息
        """
        print("=" * 60)
        print("DTCG 规则书翻译工具 (Translation Skill)")
        print("=" * 60)
        
        stats = {
            'engine': self.engine_type,
            'chunks': 0,
            'translated_chars': 0,
            'errors': 0
        }
        
        # Step 1 & 2: 提取文本
        extract_stats = self.extract_texts()
        stats.update(extract_stats)
        
        # Step 3: 构建术语表
        self.build_terminology()
        
        # Step 4: 翻译
        print("\n[4/4] 开始翻译日文规则书...")
        
        # 分割文本
        chunks = self.pdf_parser.split_text_into_chunks(
            self.japanese_text, 
            TranslationConfig.RULEBOOK_CHUNK_SIZE
        )
        stats['chunks'] = len(chunks)
        print(f"分为 {len(chunks)} 块进行翻译\n")
        
        # 翻译所有块
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            try:
                translated = self.translate_chunk(chunk, i, len(chunks))
                translated_chunks.append(translated)
                stats['translated_chars'] += len(translated)
                
                # 批次延迟
                if i % TranslationConfig.BATCH_SIZE == 0 and i < len(chunks):
                    print(f"\n  等待 {TranslationConfig.BATCH_DELAY}秒...")
                    time.sleep(TranslationConfig.BATCH_DELAY)
                    
            except Exception as e:
                print(f"\n❌ 翻译第{i}块时出错：{e}")
                stats['errors'] += 1
                translated_chunks.append(f"[翻译失败 - Chunk {i}]")
        
        # 合并翻译结果
        final_translation = "\n\n".join(translated_chunks)
        
        # 保存结果
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = TranslationConfig.get_output_path("rules")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_translation)
        
        print(f"\n{'=' * 60}")
        print(f"✅ 翻译完成！")
        print(f"输出文件：{output_file}")
        print(f"翻译字符数：{stats['translated_chars']}")
        print(f"分块数量：{stats['chunks']}")
        print(f"错误数量：{stats['errors']}")
        print(f"{'=' * 60}")
        
        stats['output_file'] = str(output_file)
        
        return stats
    
    def translate_from_text(self, japanese_text: str, 
                           output_path: Optional[str] = None) -> str:
        """
        直接从文本翻译（不需要 PDF）
        
        Args:
            japanese_text: 日文文本
            output_path: 输出文件路径（可选）
        
        Returns:
            翻译后的中文文本
        """
        self.japanese_text = japanese_text
        
        # 加载术语表
        project_root = TranslationConfig.PROJECT_ROOT
        self.terminology_manager = load_terminology_from_project(project_root)
        
        # 分割文本
        chunks = self.pdf_parser.split_text_into_chunks(
            japanese_text,
            TranslationConfig.RULEBOOK_CHUNK_SIZE
        )
        
        # 翻译
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            translated = self.translate_chunk(chunk, i, len(chunks))
            translated_chunks.append(translated)
        
        final_translation = "\n\n".join(translated_chunks)
        
        # 保存
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_translation)
        
        return final_translation


def main():
    """命令行入口"""
    import sys
    
    print("DTCG 规则书翻译工具")
    print("=" * 60)
    
    # 检查参数
    if len(sys.argv) < 3:
        print("\n用法：python rulebook_trans.py <日文 PDF 路径> [中文参考 PDF 路径] [引擎]")
        print("\n引擎选项:")
        print("  openai - OpenAI API (默认)")
        print("  gemini - Google Gemini")
        print("  qwen   - 通义千问")
        return
    
    japanese_path = sys.argv[1]
    chinese_ref = sys.argv[2] if len(sys.argv) > 2 else None
    engine = sys.argv[3] if len(sys.argv) > 3 else "openai"
    
    # 创建翻译器
    translator = RulebookTranslator(
        chinese_ref_path=chinese_ref,
        japanese_path=japanese_path,
        engine_type=engine
    )
    
    # 执行翻译
    try:
        stats = translator.translate_rulebook()
        print(f"\n✓ 翻译完成！输出：{stats['output_file']}")
    except Exception as e:
        print(f"\n❌ 翻译失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
