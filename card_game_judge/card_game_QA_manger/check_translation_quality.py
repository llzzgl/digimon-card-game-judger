"""
检查翻译质量
- 检测是否有日文残留
- 检查术语是否正确翻译
- 统计翻译覆盖率
"""
import json
import re
from pathlib import Path


def has_japanese(text):
    """检测文本中是否包含日文"""
    if not text:
        return False
    
    # 日文平假名范围
    hiragana = re.compile(r'[\u3040-\u309F]')
    # 日文片假名范围
    katakana = re.compile(r'[\u30A0-\u30FF]')
    
    return bool(hiragana.search(text) or katakana.search(text))


def check_translation_file(file_path):
    """检查翻译文件质量"""
    print("="*60)
    print(f"检查翻译文件: {file_path.name}")
    print("="*60)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        qa_list = json.load(f)
    
    print(f"\n总QA数量: {len(qa_list)}")
    
    # 统计
    total = len(qa_list)
    has_jp_question = 0
    has_jp_answer = 0
    issues = []
    
    print("\n检查日文残留...")
    for i, qa in enumerate(qa_list, 1):
        qa_num = qa.get('qa_number', 'N/A')
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        # 检查问题
        if has_japanese(question):
            has_jp_question += 1
            issues.append({
                'qa_number': qa_num,
                'type': 'question',
                'text': question[:100]
            })
        
        # 检查答案
        if has_japanese(answer):
            has_jp_answer += 1
            issues.append({
                'qa_number': qa_num,
                'type': 'answer',
                'text': answer[:100]
            })
    
    # 输出结果
    print("\n" + "="*60)
    print("检查结果")
    print("="*60)
    
    print(f"\n问题中有日文残留: {has_jp_question}/{total} ({has_jp_question/total*100:.1f}%)")
    print(f"答案中有日文残留: {has_jp_answer}/{total} ({has_jp_answer/total*100:.1f}%)")
    
    if has_jp_question == 0 and has_jp_answer == 0:
        print("\n✅ 完美！没有发现日文残留")
    else:
        print(f"\n⚠️ 发现 {len(issues)} 处日文残留")
        
        # 显示前10个问题
        print("\n前10个问题示例:")
        for issue in issues[:10]:
            print(f"\nQA #{issue['qa_number']} ({issue['type']}):")
            print(f"  {issue['text']}...")
    
    # 检查常见日文词汇
    print("\n" + "="*60)
    print("检查常见日文词汇")
    print("="*60)
    
    japanese_terms = {
        'できます': '可以',
        'できません': '不可以',
        'はい': '是的',
        'いいえ': '不是',
        'の': '的',
        'を': '',
        'が': '',
        'は': '',
        'に': '',
        'で': '',
        'と': '',
        'から': '',
        'まで': '',
        'より': '',
        'こと': '',
        'もの': '',
        'ため': '',
        'ように': '',
        'ながら': '',
        'ば': '',
        'たら': '',
        'なら': '',
        'けど': '',
        'けれど': '',
        'しかし': '',
        'でも': '',
        'そして': '',
        'または': '',
        'あるいは': '',
    }
    
    term_counts = {term: 0 for term in japanese_terms}
    
    for qa in qa_list:
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        text = question + ' ' + answer
        
        for jp_term in japanese_terms:
            if jp_term in text:
                term_counts[jp_term] += 1
    
    found_terms = {term: count for term, count in term_counts.items() if count > 0}
    
    if found_terms:
        print(f"\n⚠️ 发现以下日文词汇:")
        for term, count in sorted(found_terms.items(), key=lambda x: x[1], reverse=True):
            cn_term = japanese_terms[term]
            print(f"  {term} → {cn_term if cn_term else '(应删除)'}: {count}次")
    else:
        print("\n✅ 没有发现常见日文词汇")
    
    print("\n" + "="*60)


def compare_translations():
    """比较不同LLM的翻译结果"""
    print("\n" + "="*60)
    print("比较不同LLM的翻译结果")
    print("="*60)
    
    base_dir = Path(__file__).parent
    files = [
        base_dir / "official_qa_cn_qwen.json",
        base_dir / "official_qa_cn_gemini.json",
        base_dir / "official_qa_cn_ollama.json",
    ]
    
    for file_path in files:
        if file_path.exists():
            print(f"\n{'='*60}")
            check_translation_file(file_path)


def main():
    """主函数"""
    print("="*60)
    print("翻译质量检查工具")
    print("="*60)
    
    base_dir = Path(__file__).parent
    
    # 检查是否有翻译文件
    translation_files = list(base_dir.glob("official_qa_cn_*.json"))
    translation_files = [f for f in translation_files if 'checkpoint' not in f.name]
    
    if not translation_files:
        print("\n❌ 未找到翻译文件")
        print("请先运行翻译工具生成翻译文件")
        return
    
    print(f"\n找到 {len(translation_files)} 个翻译文件:")
    for i, f in enumerate(translation_files, 1):
        print(f"  {i}. {f.name}")
    
    print("\n选择要检查的文件:")
    print("  1. 检查所有文件")
    print("  2-N. 检查指定文件")
    
    choice = input("\n请选择 (默认1): ").strip() or "1"
    
    if choice == "1":
        for file_path in translation_files:
            check_translation_file(file_path)
    else:
        try:
            idx = int(choice) - 2
            if 0 <= idx < len(translation_files):
                check_translation_file(translation_files[idx])
            else:
                print("无效选择")
        except ValueError:
            print("无效输入")


if __name__ == "__main__":
    main()
