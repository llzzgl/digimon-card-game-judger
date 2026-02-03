@echo off
chcp 65001 > nul
cd /d "%~dp0"
python test_card_info.py
pause
