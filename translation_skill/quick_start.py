#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速开始脚本
Quick Start Script for DTCG Translation Skill

演示如何使用 Translation Skill 进行翻译
"""
import sys
import os
from pathlib import Path

# 添加当前目录到路径
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir))

# 设置环境变量（避免相对导入问题）
os.chdir(str(base_dir))


def demo_terminology():
    """演示术语管理"""
    print("=" * 60)
    print("演示 1: 术语管理")
    print("=" * 60)
    
    # 直接导入模块
    from src.utils.terminology import TerminologyManager
    
    # 创建术语管理器
    manager = TerminologyManager()
    
    # 加载术语表
    print("\n加载术语表...")
    terms = manager.load_all()
    print(f"✓ 加载了 {len(terms)} 个术语")
    
    # 查找术语
    test_terms = ["バトルエリア", "レスト", "デジモン"]
    print("\n术语查找测试:")
    for jp in test_terms:
        cn = manager.get_term(jp)
        if cn:
            print(f"  {jp} → {cn}")
    
    # 替换文本中的术语
    print("\n术语替换测试:")
    japanese_text = "バトルエリアでレスト状態のデジモン"
    replaced = manager.replace_terminology(japanese_text)
    print(f"  原文：{japanese_text}")
    print(f"  替换：{replaced}")
    
    print()


def demo_translator():
    """演示翻译器"""
    print("=" * 60)
    print("演示 2: 翻译器")
    print("=" * 60)
    
    from src.translator import Translator
    
    # 创建翻译器
    translator = Translator(default_engine="qwen")
    
    # 列出可用引擎
    print("\n可用引擎:")
    engines = translator.list_engines()
    for engine in engines:
        status = "✓" if engine['available'] else "✗"
        print(f"  {status} {engine['name']}")
    
    # 检查是否有可用引擎
    available_engine = translator.get_engine()
    if not available_engine:
        print("\n⚠️  没有可用的翻译引擎，请配置 API 密钥")
        print("   在 .env 文件中设置 DASHSCOPE_API_KEY、OPENAI_API_KEY 或 GEMINI_API_KEY")
        return
    
    # 翻译示例文本
    print("\n翻译测试:")
    test_texts = [
        "このデジモンは攻撃できない。",
        "手札から 1 枚捨てる。",
        "バトルエリアに出す。"
    ]
    
    for text in test_texts:
        try:
            result = translator.translate(text)
            print(f"  原文：{text}")
            print(f"  译文：{result}")
            print()
        except Exception as e:
            print(f"  翻译失败：{e}")
            break
    
    print()


def demo_qa_translation():
    """演示 QA 翻译"""
    print("=" * 60)
    print("演示 3: QA 翻译")
    print("=" * 60)
    
    from src.tasks.qa_trans import QATranslator
    
    # 创建翻译器
    translator = QATranslator(
        input_qa_path=str(base_dir / "data" / "input" / "sample_qa_jp.json"),
        output_qa_path=str(base_dir / "data" / "output" / "sample_qa_cn.json"),
        engine_type="qwen"
    )
    
    # 加载数据
    print("\n加载数据...")
    stats = translator.load_data()
    print(f"  术语数：{stats.get('terminology_count', 0)}")
    print(f"  卡牌数：{stats.get('card_count', 0)}")
    
    # 检查引擎
    engine = translator.translator.get_engine("qwen")
    if not engine or not engine.is_available():
        print("\n⚠️  Qwen 引擎不可用，跳过翻译演示")
        return
    
    # 翻译测试（仅前 2 条）
    print("\n翻译测试（前 2 条）...")
    try:
        result_stats = translator.translate_all(max_count=2, delay=1.0)
        print(f"\n✓ 翻译完成")
        print(f"  翻译数：{result_stats['translated']}")
        print(f"  输出：{translator.output_qa_path}")
    except Exception as e:
        print(f"\n✗ 翻译失败：{e}")
    
    print()


def demo_rulebook_translation():
    """演示规则书翻译"""
    print("=" * 60)
    print("演示 4: 规则书翻译")
    print("=" * 60)
    
    from src.utils.pdf_parser import PDFParser
    
    # 检查是否有 PDF 文件
    print("\n检查 PDF 文件...")
    # 这里只是演示，实际需要用户指定 PDF 路径
    
    # 演示文本分割
    print("\n文本分割演示:")
    parser = PDFParser()
    
    test_text = "\n\n".join([f"第{i}条规则：これは第{i}条のルール説明です。" for i in range(1, 21)])
    chunks = parser.split_text_into_chunks(test_text, max_chars=200)
    
    print(f"  原文长度：{len(test_text)} 字符")
    print(f"  分割块数：{len(chunks)} 块")
    print(f"  第一块：{chunks[0][:50]}...")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DTCG Translation Skill 快速开始")
    print("=" * 60)
    print()
    
    # 演示 1: 术语管理
    demo_terminology()
    
    # 演示 2: 翻译器
    demo_translator()
    
    # 演示 3: QA 翻译
    demo_qa_translation()
    
    # 演示 4: 规则书翻译
    demo_rulebook_translation()
    
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 配置 .env 文件中的 API 密钥")
    print("2. 准备 PDF 文件（规则书翻译）")
    print("3. 运行完整翻译任务")
    print("\n详细文档请查看：README.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
