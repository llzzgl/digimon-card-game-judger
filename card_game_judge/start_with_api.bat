@echo off
echo ============================================================
echo DTCG 裁判助手 - 使用 API 模型（稳定版）
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
    echo [警告] .env 文件不存在，请创建并配置 API 密钥
    echo [提示] 复制 .env.example 为 .env 并填写密钥
    echo.
)

echo.
echo 配置信息:
echo   模型类型：通义千问 API (qwen)
echo   说明：稳定可靠，无需本地模型
echo.

echo 正在启动服务...
echo.

python main.py

pause
