"""
清除LLM提取的检查点文件
如果你想从头开始重新提取，运行这个脚本
"""

from pathlib import Path

checkpoint_file = Path(__file__).parent / "llm_extraction_checkpoint.json"

if checkpoint_file.exists():
    checkpoint_file.unlink()
    print("✓ 检查点文件已删除")
    print("  下次运行将从头开始提取")
else:
    print("✗ 没有找到检查点文件")
    print("  无需清除")
