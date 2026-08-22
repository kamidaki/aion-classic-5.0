@echo off
title Aion Classic (EU 4.5) - Iniciar Servidores
color 0A

echo =========================================================================
echo       INICIANDO SERVIDORES AION CLASSIC 4.5 (RUST EMULATOR)
echo =========================================================================
echo.

cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo [*] Encerrando processos antigos...
taskkill /F /IM game-server.exe >nul 2>&1
taskkill /F /IM auth-server.exe >nul 2>&1
taskkill /F /IM sts-server.exe >nul 2>&1

echo [1/3] Iniciando STS Server (Porta 6600)...
start "Aion Classic - STS Server (Porta 6600)" powershell.exe -NoExit -Command ".\sts-server.exe 2>&1 | Tee-Object -FilePath logs\sts_server.log"

ping 127.0.0.1 -n 2 >nul

echo [2/3] Iniciando Auth Server (Portas 13001 e 2106)...
start "Aion Classic - Auth Server (Portas 13001 / 2106)" powershell.exe -NoExit -Command ".\auth-server.exe 2>&1 | Tee-Object -FilePath logs\auth_server.log"

ping 127.0.0.1 -n 2 >nul

echo [3/3] Iniciando Game Server (Porta 7777)...
start "Aion Classic - Game Server (Porta 7777)" powershell.exe -NoExit -Command ".\game-server.exe 2>&1 | Tee-Object -FilePath logs\game_server.log"

echo.
echo =========================================================================
echo   [+] TODOS OS SERVIDORES FORAM INICIADOS!
echo.
echo   * STS Server:   127.0.0.1:6600
echo   * Auth Server:  127.0.0.1:2106 / 13001
echo   * Game Server:  127.0.0.1:7777 (1254 NPCs)
echo.
echo   Para jogar, execute: Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
echo   Para parar, execute: deploy\PARAR_SERVIDOR.bat
echo =========================================================================
echo.
pause
