@echo off
chcp 65001 >nul
echo ========================================
echo 数码兽卡牌官方QA爬虫
echo ========================================
echo.

echo [1/3] 检查依赖...
pip install -r requirements.txt
echo.

echo [2/3] 开始爬取FAQ...
python scraper_faq.py
echo.

echo [3/3] 复制到微调目录...
python copy_to_finetune.py
echo.

echo ========================================
echo 完成！
echo ========================================
pause
