"""
简易翻译启动脚本
Easy launcher for rulebook translation
"""

import sys
import os
from pathlib import Path


def print_menu():
    print("\n" + "=" * 60)
    print("DTCG 规则书翻译工具")
    print("=" * 60)
    print("\n请选择翻译引擎：")
    print("1. OpenAI (推荐 - 稳定可靠，支持国内网络)")
    print("2. Google Gemini (需要特殊网络环境)")
    print("3. 查看两者对比")
    print("0. 退出")
    print("=" * 60)


def check_files():
    """检查必要文件是否存在"""
    chinese_ref = "数码宝贝卡牌对战 综合规则1.2（2024-02-16）.pdf"
    japanese_new = "general_rule.pdf"
    
    missing = []
    if not Path(chinese_ref).exists():
        missing.append(chinese_ref)
    if not Path(japanese_new).exists():
        missing.append(japanese_new)
    
    if missing:
        print("\n⚠️  警告：以下文件未找到：")
        for f in missing:
            print(f"   - {f}")
        print("\n请确保这些PDF文件在当前目录下。")
        return False
    
    return True


def check_api_key(key_name):
    """检查API密钥是否配置"""
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv(key_name)
    if not key or key.startswith("your"):
        print(f"\n⚠️  警告：{key_name} 未配置或无效")
        print(f"请在 .env 文件中设置正确的 {key_name}")
        return False
    
    return True


def run_openai():
    """运行 OpenAI 版本"""
    if not check_api_key("OPENAI_API_KEY"):
        return
    
    print("\n正在使用 OpenAI 进行翻译...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    from translate_rulebook_openai import main
    main()


def run_gemini():
    """运行 Gemini 版本"""
    if not check_api_key("GOOGLE_API_KEY"):
        return
    
    print("\n⚠️  注意：Google Gemini 在中国大陆可能无法访问")
    print("如果连接失败，请使用 OpenAI 版本\n")
    
    confirm = input("确认继续使用 Gemini？(y/n): ").strip().lower()
    if confirm != 'y':
        return
    
    print("\n正在使用 Google Gemini 进行翻译...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    from translate_rulebook_gemini import main
    main()


def show_comparison():
    """显示对比信息"""
    comparison_file = "translate_comparison.md"
    if Path(comparison_file).exists():
        with open(comparison_file, 'r', encoding='utf-8') as f:
            print("\n" + f.read())
    else:
        print("\n对比文件未找到")


def main():
    print("\n欢迎使用 DTCG 规则书翻译工具！")
    
    # 检查文件
    if not check_files():
        print("\n请先准备好必要的PDF文件，然后重新运行此脚本。")
        return
    
    while True:
        print_menu()
        choice = input("\n请输入选项 (0-3): ").strip()
        
        if choice == "1":
            run_openai()
            break
        elif choice == "2":
            run_gemini()
            break
        elif choice == "3":
            show_comparison()
            input("\n按回车键继续...")
        elif choice == "0":
            print("\n再见！")
            break
        else:
            print("\n❌ 无效选项，请重新选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
