"""
测试LLM配置
"""

print("=" * 60)
print("测试LLM配置")
print("=" * 60)

# 测试导入
try:
    from llm_config import LLM_TYPE, MODEL_CONFIG, EXTRACTION_CONFIG
    print(f"✓ 配置文件加载成功")
    print(f"  LLM类型: {LLM_TYPE}")
    print(f"  模型配置: {MODEL_CONFIG.get(LLM_TYPE, {})}")
    print(f"  提取配置: {EXTRACTION_CONFIG}")
except ImportError as e:
    print(f"✗ 配置文件加载失败: {e}")
    print("  将使用默认配置")

print()

# 测试环境变量
from pathlib import Path
from dotenv import load_dotenv
import os

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
env_path = project_root / "card_game_judge" / ".env"

print(f"环境变量文件: {env_path}")
print(f"文件存在: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("✓ 环境变量已加载")
    
    # 检查API密钥
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print()
    print("API密钥状态:")
    print(f"  DASHSCOPE_API_KEY (通义千问): {'✓ 已设置' if dashscope_key else '✗ 未设置'}")
    if dashscope_key:
        print(f"    值: {dashscope_key[:10]}...")
    
    print(f"  GOOGLE_API_KEY (Gemini): {'✓ 已设置' if google_key else '✗ 未设置'}")
    if google_key:
        print(f"    值: {google_key[:10]}...")
    
    print(f"  OPENAI_API_KEY (OpenAI): {'✓ 已设置' if openai_key else '✗ 未设置'}")
    if openai_key:
        print(f"    值: {openai_key[:10]}...")

print()

# 测试OpenAI库
try:
    from openai import OpenAI
    print("✓ openai库已安装")
except ImportError:
    print("✗ openai库未安装")
    print("  请运行: pip install openai")

print()

# 测试通义千问连接
try:
    from llm_config import LLM_TYPE
    if LLM_TYPE == "qwen":
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        if dashscope_key:
            print("测试通义千问连接...")
            from openai import OpenAI
            client = OpenAI(
                api_key=dashscope_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            print("✓ 通义千问客户端初始化成功")
            
            # 测试简单调用
            try:
                response = client.chat.completions.create(
                    model="qwen-turbo",
                    messages=[{"role": "user", "content": "你好"}],
                    max_tokens=10
                )
                print("✓ 通义千问API调用成功")
                print(f"  响应: {response.choices[0].message.content}")
            except Exception as e:
                print(f"✗ 通义千问API调用失败: {e}")
        else:
            print("✗ 未设置DASHSCOPE_API_KEY，无法测试")
except Exception as e:
    print(f"✗ 测试失败: {e}")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
