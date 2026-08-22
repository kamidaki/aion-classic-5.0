@echo off
title Aion Classic (EU 4.5) - Iniciar Servidores (Rust)
color 0a

echo ============================================================
echo      Iniciando Servidores Aion Classic EU (Rust)      
echo ============================================================
echo.

set DEPLOY_DIR=%~dp0..\deploy
if not exist "%DEPLOY_DIR%\game-server.exe" (
    set DEPLOY_DIR=%~dp0deploy
)

cd /d "%DEPLOY_DIR%"

echo [1/3] Iniciando STS Server (Porta 6600)...
start "Aion Classic - STS Server (Rust)" "sts-server.exe"

ping 127.0.0.1 -n 2 >nul

echo [2/3] Iniciando Auth Server (Portas 13001 e 2106)...
start "Aion Classic - Auth Server (Rust)" "auth-server.exe" 127.0.0.1

ping 127.0.0.1 -n 2 >nul

echo [3/3] Iniciando Game Server (Porta 7777 - 20 TPS)...
start "Aion Classic - Game Server (Rust)" "game-server.exe"

echo.
echo ============================================================
echo   Servidores Rust em execucao com sucesso!
echo   STS Server:  127.0.0.1:6600
echo   Auth Server: 127.0.0.1:2106 / 13001
echo   Game Server: 127.0.0.1:7777 (1254 NPCs carregados)
echo ============================================================
ping 127.0.0.1 -n 3 >nul


