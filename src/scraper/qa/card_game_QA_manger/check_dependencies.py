"""
检查翻译工具所需的依赖是否已安装
"""

def check_dependencies():
    """检查所有必需的依赖"""
    print("="*60)
    print("检查依赖库")
    print("="*60)
    
    dependencies = {
        'openai': {
            'required_for': ['Qwen', 'Ollama'],
            'install': 'pip install openai'
        },
        'google.generativeai': {
            'required_for': ['Gemini'],
            'install': 'pip install google-generativeai'
        },
        'dotenv': {
            'required_for': ['所有LLM'],
            'install': 'pip install python-dotenv'
        },
        'pathlib': {
            'required_for': ['所有LLM'],
            'install': '内置库，无需安装'
        },
        'json': {
            'required_for': ['所有LLM'],
            'install': '内置库，无需安装'
        }
    }
    
    missing = []
    installed = []
    
    for module_name, info in dependencies.items():
        try:
            if '.' in module_name:
                # 处理子模块导入
                parts = module_name.split('.')
                __import__(parts[0])
                mod = __import__(module_name)
                for part in parts[1:]:
                    mod = getattr(mod, part)
            else:
                __import__(module_name)
            
            print(f"✓ {module_name:25} - 已安装")
            installed.append(module_name)
            
            # 尝试获取版本
            try:
                if module_name == 'openai':
                    import openai
                    print(f"  版本: {openai.__version__}")
                elif module_name == 'google.generativeai':
                    import google.generativeai as genai
                    if hasattr(genai, '__version__'):
                        print(f"  版本: {genai.__version__}")
                elif module_name == 'dotenv':
                    import dotenv
                    if hasattr(dotenv, '__version__'):
                        print(f"  版本: {dotenv.__version__}")
            except:
                pass
                
        except ImportError:
            print(f"✗ {module_name:25} - 未安装")
            print(f"  用途: {', '.join(info['required_for'])}")
            print(f"  安装: {info['install']}")
            missing.append((module_name, info))
    
    print("\n" + "="*60)
    print("检查结果")
    print("="*60)
    print(f"已安装: {len(installed)}/{len(dependencies)}")
    print(f"缺失: {len(missing)}/{len(dependencies)}")
    
    if missing:
        print("\n需要安装的库:")
        for module_name, info in missing:
            print(f"  - {module_name}")
            print(f"    {info['install']}")
        
        print("\n快速安装命令:")
        install_commands = set(info['install'] for _, info in missing if 'pip install' in info['install'])
        for cmd in install_commands:
            print(f"  {cmd}")
    else:
        print("\n✓ 所有依赖已安装！")
    
    print("="*60)
    
    return len(missing) == 0


def check_llm_availability():
    """检查各个LLM的可用性"""
    print("\n" + "="*60)
    print("检查LLM可用性")
    print("="*60)
    
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    # 加载环境变量
    base_dir = Path(__file__).parent.parent
    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    llms = {
        'Qwen (通义千问)': {
            'env_var': 'DASHSCOPE_API_KEY',
            'required_lib': 'openai'
        },
        'Gemini': {
            'env_var': ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],
            'required_lib': 'google.generativeai'
        },
        'Ollama (本地)': {
            'env_var': None,
            'required_lib': 'openai',
            'note': '需要本地运行Ollama服务'
        }
    }
    
    for llm_name, config in llms.items():
        print(f"\n{llm_name}:")
        
        # 检查库
        lib = config['required_lib']
        try:
            if '.' in lib:
                parts = lib.split('.')
                __import__(parts[0])
            else:
                __import__(lib)
            print(f"  ✓ 依赖库 ({lib}) 已安装")
            lib_ok = True
        except ImportError:
            print(f"  ✗ 依赖库 ({lib}) 未安装")
            lib_ok = False
        
        # 检查环境变量
        env_var = config.get('env_var')
        if env_var:
            if isinstance(env_var, list):
                # 多个可选的环境变量
                found = False
                for var in env_var:
                    if os.getenv(var):
                        print(f"  ✓ API密钥 ({var}) 已配置")
                        found = True
                        break
                if not found:
                    print(f"  ✗ API密钥未配置 (需要: {' 或 '.join(env_var)})")
                env_ok = found
            else:
                # 单个环境变量
                if os.getenv(env_var):
                    print(f"  ✓ API密钥 ({env_var}) 已配置")
                    env_ok = True
                else:
                    print(f"  ✗ API密钥 ({env_var}) 未配置")
                    env_ok = False
        else:
            env_ok = True
        
        # 额外说明
        if 'note' in config:
            print(f"  ℹ {config['note']}")
        
        # 总结
        if lib_ok and env_ok:
            print(f"  ✓ {llm_name} 可用")
        else:
            print(f"  ✗ {llm_name} 不可用")
    
    print("="*60)


if __name__ == "__main__":
    deps_ok = check_dependencies()
    
    if deps_ok:
        try:
            check_llm_availability()
        except Exception as e:
            print(f"\n检查LLM可用性时出错: {e}")
    else:
        print("\n请先安装缺失的依赖库，然后重新运行此脚本。")
