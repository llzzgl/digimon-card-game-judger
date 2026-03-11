"""
网络连接检查脚本

检查是否能够访问 Hugging Face 镜像站
"""
import os
import sys

def check_network():
    """检查网络连接"""
    print("=" * 60)
    print("网络连接检查")
    print("=" * 60)
    
    # 检查环境变量
    print("\n1. 检查环境变量:")
    hf_endpoint = os.environ.get("HF_ENDPOINT", "未设置")
    print(f"   HF_ENDPOINT = {hf_endpoint}")
    
    if hf_endpoint == "未设置":
        print("   ⚠️  建议设置: set HF_ENDPOINT=https://hf-mirror.com")
    
    # 测试连接
    print("\n2. 测试连接:")
    
    urls = [
        ("Hugging Face 官方", "https://huggingface.co"),
        ("Hugging Face 镜像", "https://hf-mirror.com"),
    ]
    
    for name, url in urls:
        print(f"\n   测试 {name}: {url}")
        try:
            import urllib.request
            import socket
            
            # 设置超时
            socket.setdefaulttimeout(5)
            
            # 尝试连接
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5)
            
            print(f"   ✅ 连接成功 (状态码: {response.status})")
            
        except Exception as e:
            print(f"   ❌ 连接失败: {str(e)}")
    
    # 检查模型缓存
    print("\n3. 检查模型缓存:")
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    model_dir = os.path.join(cache_dir, "models--BAAI--bge-m3")
    
    if os.path.exists(model_dir):
        print(f"   ✅ 找到模型缓存: {model_dir}")
        
        # 检查关键文件
        key_files = [
            "pytorch_model.bin",
            "config.json",
            "tokenizer_config.json"
        ]
        
        for file in key_files:
            file_path = None
            for root, dirs, files in os.walk(model_dir):
                if file in files:
                    file_path = os.path.join(root, file)
                    break
            
            if file_path:
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"   ✅ {file}: {size:.2f} MB")
            else:
                print(f"   ❌ {file}: 未找到")
    else:
        print(f"   ❌ 未找到模型缓存: {model_dir}")
        print("   需要下载模型")
    
    # 建议
    print("\n" + "=" * 60)
    print("建议:")
    print("=" * 60)
    
    if hf_endpoint == "未设置":
        print("1. 设置镜像环境变量:")
        print("   Windows CMD:")
        print("   set HF_ENDPOINT=https://hf-mirror.com")
        print()
        print("   Windows PowerShell:")
        print("   $env:HF_ENDPOINT=\"https://hf-mirror.com\"")
        print()
    
    if not os.path.exists(model_dir):
        print("2. 首次运行需要下载模型（约 2.27GB）")
        print("   请确保网络连接稳定")
        print()
        print("3. 或手动下载模型:")
        print("   访问: https://hf-mirror.com/BAAI/bge-m3")
        print("   下载所有文件到:")
        print(f"   {model_dir}")
        print()
    
    print("4. 或使用 API 服务代替本地模型:")
    print("   - OpenAI Embeddings")
    print("   - Google Gemini Embeddings")
    print()
    print("=" * 60)


if __name__ == "__main__":
    check_network()
