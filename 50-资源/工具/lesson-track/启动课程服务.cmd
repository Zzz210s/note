@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 课程服务:打开 http://127.0.0.1:8787/ (VS Code 里用 Simple Browser 打开)
echo 关掉这个窗口即停止。
set PYTHONIOENCODING=utf-8
python -B server.py
pause
