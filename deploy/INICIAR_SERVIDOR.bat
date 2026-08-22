@echo off
chcp 65001 > nul
title Aion Classic 4.5 - Servidor Rust
setlocal

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "iniciar.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pressione qualquer tecla para fechar...
    pause > nul
)
