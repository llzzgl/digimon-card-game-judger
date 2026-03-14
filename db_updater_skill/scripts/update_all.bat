@echo off
chcp 65001 >nul
echo ============================================================
echo DTCG Database Updater - 一键更新脚本
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [完成] Python 环境正常

echo.
echo [2/4] 安装依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [完成] 依赖安装完成

echo.
echo [3/4] 开始更新数据...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 数据更新失败
    pause
    exit /b 1
)

echo.
echo [4/4] 验证输出...
if exist "..\skill\data\cards.json" (
    echo [完成] 卡牌数据库已更新
) else (
    echo [警告] 卡牌数据库未生成
)

if exist "..\skill\data\rulings.json" (
    echo [完成] QA 数据库已更新
) else (
    echo [警告] QA 数据库未生成
)

echo.
echo ============================================================
echo 更新完成！
echo ============================================================
echo.
pause
