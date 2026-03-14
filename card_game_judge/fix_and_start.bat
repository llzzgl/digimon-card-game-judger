@echo off
echo ============================================================
echo DTCG 裁判助手 - 自动修复并启动
echo ============================================================
echo.

echo 检测到 LoRA 加载问题，正在自动修复...
echo.

echo 步骤 1/3: 合并 LoRA 权重...
python merge_lora.py
if errorlevel 1 (
    echo.
    echo [错误] 合并失败，尝试使用 API 模型...
    echo.
    set LLM_MODEL=qwen
    goto start_service
)

echo.
echo 步骤 2/3: 更新配置...
REM 从 .env 读取配置，不直接修改
echo [提示] 请手动更新 .env 文件中的 LoRA 配置
echo.

echo 步骤 3/3: 启动服务...
:start_service
python main.py

pause
