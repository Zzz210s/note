@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 0-Note 课程服务(关掉这个窗口即停止)

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [错误] 没找到 python。请确认 python 在 PATH 里(在 PowerShell 里敲 python --version 试一下)。
  echo.
  pause
  exit /b 1
)

echo ============================================================
echo  0-Note 课程服务
echo  在 VS Code 里按 Ctrl+Shift+P,运行 Simple Browser: Show,
echo  地址填:http://127.0.0.1:8787/
echo  ^(次数会写进各项目的 00-索引.md;关掉本窗口即停止^)
echo ============================================================
echo.
set PYTHONIOENCODING=utf-8
python -B server.py
echo.
echo 服务已停止(若上面有报错,把它截图发我)。
pause
