@echo off
setlocal
chcp 65001 >nul
title Aion Classic 5.0 - Coletor de Spawns em Tempo Real
cd /d "%~dp0"

python "%~dp0live_spawn_collector.py" %*

if errorlevel 1 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a execucao do coletor.
    pause
)
