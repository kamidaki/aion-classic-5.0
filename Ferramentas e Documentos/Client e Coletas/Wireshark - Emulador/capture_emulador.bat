@echo off
setlocal
chcp 65001 >nul
title Aion Classic 5.0 - Captura do Emulador (loopback)
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0capture_emulador.ps1" %*

if errorlevel 1 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a execucao da captura.
    pause
)
