"""
测试通义千问API连接
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import time

def test_qwen_api():
    """测试Qwen API"""
    print("="*60)
    print("测试通义千问API连接")
    print("="*60)
    
    # 加载环境变量
    base_dir = Path(__file__).parent.parent
    env_path = base_dir / ".env"
    
    print(f"\n1. 加载环境变量: {env_path}")
    if env_path.exists():
        load_dotenv(env_path)
        print("   ✓ .env文件已加载")
    else:
        print("   ✗ .env文件不存在")
        return
    
    # 检查API密钥
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("\n   ✗ 未找到DASHSCOPE_API_KEY")
        print("   请在.env文件中添加: DASHSCOPE_API_KEY=sk-xxxxx")
        return
    
    print(f"   ✓ API密钥已加载: {api_key[:10]}...{api_key[-4:]}")
    
    # 初始化客户端
    print("\n2. 初始化OpenAI客户端")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        print("   ✓ 客户端初始化成功")
    except Exception as e:
        print(f"   ✗ 客户端初始化失败: {e}")
        return
    
    # 测试简单调用
    print("\n3. 测试简单API调用")
    print("   发送测试消息: '你好，请回复OK'")
    
    try:
        start_time = time.time()
        print("   等待响应...", end='', flush=True)
        
        response = client.chat.completions.create(
            model="qwen3.5-flash-2026-02-23",
            messages=[
                {"role": "user", "content": "你好，请回复OK"}
            ],
            temperature=0.3,
            max_tokens=100,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f" 完成 ({elapsed:.1f}秒)")
        
        result = response.choices[0].message.content
        print(f"   ✓ API响应: {result}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f" 失败 ({elapsed:.1f}秒)")
        print(f"   ✗ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试翻译任务
    print("\n4. 测试翻译任务")
    test_text = "このカードの【登場時】効果は、自分のデジモンをレストできますか？"
    print(f"   日文: {test_text}")
    
    try:
        start_time = time.time()
        print("   翻译中...", end='', flush=True)
        
        response = client.chat.completions.create(
            model="qwen3.5-flash-2026-02-23", 
            messages=[
                {"role": "system", "content": "你是一位专业的日文翻译专家。请将日文完整翻译成中文，不要保留任何日文。"},
                {"role": "user", "content": f"请翻译：{test_text}"}
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f" 完成 ({elapsed:.1f}秒)")
        
        result = response.choices[0].message.content
        print(f"   ✓ 翻译结果: {result}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f" 失败 ({elapsed:.1f}秒)")
        print(f"   ✗ 翻译失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("✓ 所有测试通过！API连接正常")
    print("="*60)


if __name__ == "__main__":
    test_qwen_api()
