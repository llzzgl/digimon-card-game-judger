@echo off
echo ============================================================
echo DTCG 裁判助手 - 使用 API 模型（稳定版）
echo ============================================================
echo.

REM 临时使用 API 模型，避免微调模型加载问题
set LLM_MODEL=qwen
set DASHSCOPE_API_KEY=sk-87703f92f5894da3a5fef9e750fa38c9

echo 配置信息:
echo   模型类型: 通义千问 API (qwen)
echo   说明: 稳定可靠，无需本地模型
echo.

echo 正在启动服务...
echo.

python main.py

pause
