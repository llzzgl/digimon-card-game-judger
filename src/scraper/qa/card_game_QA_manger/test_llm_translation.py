"""
测试LLM翻译效果
翻译3条QA查看质量
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai


def test_translation():
    """测试翻译效果"""
    
    # 加载环境变量
    load_dotenv(Path(__file__).parent.parent / '.env')
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ 错误: 未找到API密钥")
        print("请在 .env 文件中设置 GOOGLE_API_KEY 或 GEMINI_API_KEY")
        return
    
    # 初始化模型
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 加载术语表
    base_dir = Path(__file__).parent.parent.parent
    terminology_path = base_dir / "digimon_data" / "dtcg_terminology.json"
    
    with open(terminology_path, 'r', encoding='utf-8') as f:
        terminology_data = json.load(f)
    
    # 构建术语列表
    term_map = {}
    for category, terms in terminology_data.items():
        if isinstance(terms, dict):
            term_map.update(terms)
    
    common_terms = []
    for jp, cn in list(term_map.items())[:50]:
        common_terms.append(f"  - {jp} → {cn}")
    terms_text = "\n".join(common_terms)
    
    # 构建提示词
    prompt_template = f"""你是一位专业的数码宝贝卡牌游戏翻译专家。你的任务是将日文QA翻译成高质量的中文，要求：

## 翻译原则

1. **信达雅**: 准确传达原意，表达流畅自然，符合中文习惯
2. **通俗易懂**: 使用简洁明了的语言，避免生硬的直译
3. **专业准确**: 游戏专有名词必须使用标准译名

## 专有名词对照表（必须严格遵守）

{terms_text}

## 翻译要求

1. **效果标记**: 【登場時】→【登场时】、【進化時】→【进化时】等，必须使用中文方括号
2. **语气**: 问句保持疑问语气，答句保持陈述语气
3. **数值**: DP、Lv.等保持原样
4. **流畅度**: 翻译后的句子要符合中文语法，读起来自然流畅

## 示例

**日文**: このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
**中文**: 这张卡的【登场时】【进化时】效果，可以休眠自己或对手的任意数码宝贝吗？

**日文**: はい、レストできます。
**中文**: 是的，可以休眠。

请翻译以下内容，只输出翻译结果，不要添加任何解释：

---

{{text}}"""
    
    # 加载测试数据
    qa_path = base_dir / "card_game_judge" / "card_game_QA_manger" / "official_qa_jp.json"
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_list = json.load(f)
    
    # 测试翻译前3条
    print("="*60)
    print("LLM翻译质量测试")
    print("="*60)
    print(f"\n使用模型: Gemini 2.5 Flash")
    print(f"测试数量: 3条\n")
    
    for i, qa in enumerate(qa_list[:3], 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/3 - QA #{qa.get('qa_number', 'N/A')}")
        print(f"{'='*60}")
        
        # 翻译问题
        question_jp = qa.get('question', '')
        print(f"\n【原始问题】\n{question_jp}")
        
        try:
            prompt = prompt_template.replace('{{text}}', question_jp)
            response = model.generate_content(prompt)
            question_cn = response.text.strip()
            print(f"\n【翻译问题】\n{question_cn}")
        except Exception as e:
            print(f"\n❌ 翻译失败: {e}")
            continue
        
        # 翻译答案
        answer_jp = qa.get('answer', '')
        print(f"\n【原始答案】\n{answer_jp}")
        
        try:
            prompt = prompt_template.replace('{{text}}', answer_jp)
            response = model.generate_content(prompt)
            answer_cn = response.text.strip()
            print(f"\n【翻译答案】\n{answer_cn}")
        except Exception as e:
            print(f"\n❌ 翻译失败: {e}")
            continue
        
        print(f"\n{'='*60}\n")
        
        # 等待一下避免限流
        if i < 3:
            import time
            time.sleep(2)
    
    print("\n✓ 测试完成！")
    print("\n如果翻译质量满意，可以运行完整翻译:")
    print("  python translate_qa_with_llm.py")


if __name__ == "__main__":
    test_translation()
