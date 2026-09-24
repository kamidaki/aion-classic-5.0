@echo off
setlocal
chcp 65001 >nul
title Aion Classic 5.0 - Suite de Captura e Gravador de Trafego (Wireshark)
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0capture_5.0.ps1" %*

if errorlevel 1 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a execucao da captura.
    pause
)
