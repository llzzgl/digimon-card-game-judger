@echo off
chcp 65001 >nul
echo ========================================
echo 高质量LLM翻译工具
echo ========================================
echo.
echo 使用Gemini 2.0 Flash进行翻译
echo 确保翻译信达雅，通俗易懂
echo.

python translate_qa_with_llm.py

echo.
pause
