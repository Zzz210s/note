@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo 正在读 VS Code 集成浏览器的访问历史,并把次数写回各项目 00-索引.md ...
python -B track_lib.py --sync
echo.
pause
