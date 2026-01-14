"""
DTCG 卡牌翻译主程序
运行此脚本翻译所有卡牌数据
"""

import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from card_translator import CardTranslator


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG 卡牌数据翻译工具")
    print("=" * 60)
    
    # 配置路径
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "digimon_card_data"
    output_dir = base_dir / "digimon_data" / "translated_cards"
    name_mapping_path = base_dir / "digimon_data" / "digimon_name_mapping.json"
    
    print(f"\n输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"名称映射: {name_mapping_path}")
    
    # 检查输入目录
    if not input_dir.exists():
        print(f"\n❌ 错误: 输入目录不存在: {input_dir}")
        return
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 询问是否使用AI翻译
    use_ai = True
    ai_provider = "gemini"
    
    print("\n翻译模式选择:")
    print("1. 使用 Gemini AI 翻译 (推荐，需要 GOOGLE_API_KEY)")
    print("2. 使用 OpenAI 翻译 (需要 OPENAI_API_KEY)")
    print("3. 仅使用术语表翻译 (不使用AI)")
    
    try:
        choice = input("\n请选择 (1/2/3，默认1): ").strip() or "1"
        
        if choice == "1":
            use_ai = True
            ai_provider = "gemini"
        elif choice == "2":
            use_ai = True
            ai_provider = "openai"
        else:
            use_ai = False
            ai_provider = None
    except:
        pass
    
    print(f"\n使用AI翻译: {use_ai}")
    if use_ai:
        print(f"AI提供商: {ai_provider}")
    
    # 创建翻译器
    translator = CardTranslator(
        name_mapping_path=str(name_mapping_path) if name_mapping_path.exists() else None,
        use_ai=use_ai,
        ai_provider=ai_provider
    )
    
    # 翻译所有卡牌
    print("\n开始翻译...")
    translator.translate_all_cards(str(input_dir), str(output_dir))
    
    print("\n" + "=" * 60)
    print("✅ 翻译完成！")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
