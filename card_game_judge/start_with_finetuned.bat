@echo off
echo ============================================================
echo DTCG 裁判助手 - 使用微调模型
echo ============================================================
echo.

REM 从 .env 文件加载环境变量
if exist ".env" (
    echo [加载] 从 .env 加载配置...
    for /f "delims=" %%a in ('findstr /v "^#" .env ^| findstr /v "^$"') do (
        for /f "tokens=1,* delims==" %%b in ("%%a") do (
            set "%%b=%%c"
        )
    )
    echo [完成] 配置加载成功
) else (
    echo [警告] .env 文件不存在，请创建并配置
    echo [提示] 复制 .env.example 为 .env 并填写配置
    echo.
)

REM 设置默认值（如果 .env 中未定义）
if "%LLM_MODEL%"=="" set LLM_MODEL=finetuned
if "%FINETUNED_LORA_PATH%"=="" set FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
if "%FINETUNED_BASE_MODEL%"=="" set FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct

echo.
echo 配置信息:
echo   模型类型：%LLM_MODEL%
echo   LoRA 路径：%FINETUNED_LORA_PATH%
echo   基础模型：%FINETUNED_BASE_MODEL%
echo.

echo 正在启动服务...
echo.

python main.py

pause
