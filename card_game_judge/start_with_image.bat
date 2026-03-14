@echo off
chcp 65001 >nul
echo ============================================
echo 卡牌游戏智能裁判 - 增强版 (支持图片识别)
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [检查] Python 已安装
echo.

REM 检查依赖
echo [检查] 检查依赖...
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo [警告] Pillow 未安装，正在安装...
    pip install Pillow
)

python -c "import google.generativeai" >nul 2>&1
if errorlevel 1 (
    echo [警告] google-generativeai 未安装，正在安装...
    pip install google-generativeai
)

echo [完成] 依赖检查完成
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo [警告] .env 文件不存在
    echo [提示] 请配置 GEMINI_API_KEY 以启用图片识别功能
    echo [提示] 复制 .env.example 为 .env 并填写密钥
    echo.
) else (
    echo [加载] 从 .env 加载配置...
    for /f "delims=" %%a in ('findstr /v "^#" .env ^| findstr /v "^$"') do (
        for /f "tokens=1,* delims==" %%b in ("%%a") do (
            set "%%b=%%c"
        )
    )
    echo [完成] 配置加载成功
    echo.
)

REM 启动服务
echo ============================================
echo 启动服务...
echo 访问地址：http://localhost:8000
echo API 文档：http://localhost:8000/docs
echo ============================================
echo.

python main.py

pause
