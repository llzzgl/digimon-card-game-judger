# 抑制各种警告信息
import warnings
import os

# 在导入其他库之前设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用 Hugging Face 镜像
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 抑制 deprecation 警告
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*CryptographyDeprecationWarning.*")
warnings.filterwarnings("ignore", message=".*ARC4.*")
warnings.filterwarnings("ignore", message=".*torch.classes.*")

import uvicorn
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional, List


def batch_import_files(
    directory: str,
    doc_type: str = "rule",
    tags: str = "",
    file_pattern: str = "*.json",
    title_prefix: str = "",
    title_suffix: str = ""
):
    """
    批量导入目录中的文件到知识库
    
    Args:
        directory: 文件目录路径
        doc_type: 文档类型 (rule/ruling/case)
        tags: 标签，逗号分隔
        file_pattern: 文件匹配模式
        title_prefix: 从文件名中移除的前缀
        title_suffix: 从文件名中移除的后缀
    """
    from app.vector_store import vector_store
    from app.pdf_processor import extract_text_from_bytes
    from app.models import DocumentType, DocumentMetadata
    
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"错误: 目录不存在 - {directory}")
        return
    
    files = list(dir_path.glob(file_pattern))
    if not files:
        print(f"未找到匹配 {file_pattern} 的文件")
        return
    
    print(f"找到 {len(files)} 个文件待导入...")
    
    # 解析文档类型
    try:
        dtype = DocumentType(doc_type)
    except ValueError:
        print(f"错误: 无效的文档类型 '{doc_type}'，可选: rule, ruling, case")
        return
    
    # 解析标签
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    success_count = 0
    fail_count = 0
    
    for file_path in files:
        try:
            # 生成标题
            title = file_path.stem  # 去掉扩展名
            if title_prefix and title.startswith(title_prefix):
                title = title[len(title_prefix):]
            if title_suffix and title.endswith(title_suffix):
                title = title[:-len(title_suffix)]
            
            # 读取文件内容
            content = file_path.read_bytes()
            text = extract_text_from_bytes(content, file_path.name)
            
            if not text.strip():
                print(f"  跳过 (无内容): {file_path.name}")
                fail_count += 1
                continue
            
            # 创建元数据
            metadata = DocumentMetadata(
                doc_type=dtype,
                title=title,
                source=str(file_path),
                tags=tag_list
            )
            
            # 添加到向量库
            result = vector_store.add_document(text, metadata)
            print(f"  ✓ {title} ({result['chunk_count']} chunks)")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ {file_path.name}: {e}")
            fail_count += 1
    
    print(f"\n导入完成: 成功 {success_count}, 失败 {fail_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="卡牌游戏智能裁判")
    parser.add_argument("--mode", type=str, default="web", choices=["web", "streamlit", "api"],
                        help="启动模式: web(推荐,FastAPI+HTML), streamlit(旧UI), api(仅API)")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    
    # 批量导入参数
    parser.add_argument("--batch-import", type=str, metavar="DIR", help="批量导入目录中的文件")
    parser.add_argument("--doc-type", type=str, default="rule", help="文档类型: rule/ruling/case")
    parser.add_argument("--tags", type=str, default="", help="标签，逗号分隔")
    parser.add_argument("--pattern", type=str, default="*.json", help="文件匹配模式")
    parser.add_argument("--remove-prefix", type=str, default="", help="从文件名移除的前缀")
    parser.add_argument("--remove-suffix", type=str, default="", help="从文件名移除的后缀")
    
    # 兼容旧参数
    parser.add_argument("--no_ui", action="store_true", help="(已废弃) 使用 --mode api 代替")
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if args.batch_import:
        # 批量导入模式
        batch_import_files(
            directory=args.batch_import,
            doc_type=args.doc_type,
            tags=args.tags,
            file_pattern=args.pattern,
            title_prefix=args.remove_prefix,
            title_suffix=args.remove_suffix
        )
    elif args.no_ui or args.mode == "api":
        # 仅 API 模式
        print(f"🚀 启动 API 服务: http://localhost:{args.port}")
        print(f"📖 API 文档: http://localhost:{args.port}/docs")
        uvicorn.run("app.api:app", host="0.0.0.0", port=args.port, reload=False)
    elif args.mode == "streamlit":
        # Streamlit 模式 (旧UI，可能卡顿)
        print("⚠️  Streamlit 模式可能会卡顿，推荐使用 --mode web")
        ui_path = os.path.join(script_dir, "app", "web_ui.py")
        env = os.environ.copy()
        env["PYTHONWARNINGS"] = "ignore"
        subprocess.run([sys.executable, "-m", "streamlit", "run", 
                       ui_path, "--server.port", str(args.port)], env=env)
    else:
        # 默认: FastAPI + HTML 前端 (推荐)
        print(f"🎴 卡牌游戏智能裁判")
        print(f"🌐 打开浏览器访问: http://localhost:{args.port}")
        print(f"📖 API 文档: http://localhost:{args.port}/docs")
        print(f"⏳ 首次启动需要加载模型，请稍候...")
        uvicorn.run("app.api:app", host="0.0.0.0", port=args.port, reload=False)
