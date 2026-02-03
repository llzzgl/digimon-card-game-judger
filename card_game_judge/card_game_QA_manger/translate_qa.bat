@echo off
chcp 65001 >nul
echo ========================================
echo 日文QA翻译工具
echo ========================================
echo.
echo 正在运行本地翻译脚本...
echo.

python translate_qa_local.py

echo.
echo ========================================
echo 翻译完成！
echo ========================================
echo.
echo 输出文件: official_qa_cn.json
echo.
pause
