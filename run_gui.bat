@echo off
chcp 65001 >nul
title PDF to DOCX Studio
cd /d "%~dp0"

python main.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Lỗi] Quá trình thực thi gặp lỗi.
    pause
)
