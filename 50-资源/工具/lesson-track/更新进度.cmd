@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo 1/2 读取 VS Code 集成浏览器的访问历史 ...
python -B track_lib.py --sync
echo.
echo 2/2 按阅读次数给课件改名(读过的排到没读过的下面)...
python -B rename_by_count.py --apply
echo.
echo 完成。刷新资源管理器 / Obsidian 就能看到新名字。
pause
