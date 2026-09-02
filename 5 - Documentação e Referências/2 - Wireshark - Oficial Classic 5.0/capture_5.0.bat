@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0capture_5.0.ps1" %*

if errorlevel 1 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a execucao da captura.
    pause
)
