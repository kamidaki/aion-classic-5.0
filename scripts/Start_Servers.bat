@echo off
chcp 65001 > nul
title Aion Classic (EU 4.5) - Iniciar Servidores (Rust Deploy)
color 0b

echo =========================================================================
echo       INICIANDO SERVIDORES AION CLASSIC 4.5 (RUST EMULATOR)
echo =========================================================================
echo.

set DEPLOY_DIR=%~dp0..\deploy
if not exist "%DEPLOY_DIR%\game-server.exe" (
    set DEPLOY_DIR=%~dp0deploy
)

cd /d "%DEPLOY_DIR%"

if not exist "logs" (
    mkdir "logs"
)

echo [*] Encerrando instâncias antigas de servidores se houver...
taskkill /F /IM game-server.exe 2>nul
taskkill /F /IM auth-server.exe 2>nul
taskkill /F /IM sts-server.exe 2>nul
taskkill /F /IM launcher.exe 2>nul
echo.

echo [1/3] Iniciando STS Server (Porta 6600)...
start "Aion Classic - STS Server (6600)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Aion Classic - STS Server (Porta 6600)'; Write-Host '=== STS SERVER INICIADO ===' -ForegroundColor Cyan; & '.\sts-server.exe' 2>&1 | Tee-Object -FilePath 'logs\sts_server.log'"

ping 127.0.0.1 -n 2 >nul

echo [2/3] Iniciando Auth Server (Portas 13001 e 2106)...
start "Aion Classic - Auth Server (2106/13001)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Aion Classic - Auth Server (Portas 13001 / 2106)'; Write-Host '=== AUTH SERVER INICIADO ===' -ForegroundColor Yellow; & '.\auth-server.exe' '127.0.0.1' 2>&1 | Tee-Object -FilePath 'logs\auth_server.log'"

ping 127.0.0.1 -n 2 >nul

echo [3/3] Iniciando Game Server (Porta 7777 - 20 TPS)...
start "Aion Classic - Game Server (7777)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Aion Classic - Game Server (Porta 7777 - 20 TPS)'; Write-Host '=== GAME SERVER INICIADO ===' -ForegroundColor Green; & '.\game-server.exe' 2>&1 | Tee-Object -FilePath 'logs\game_server.log'"

echo.
echo =========================================================================
echo   [+] TODOS OS SERVIDORES RUST FORAM INICIADOS COM SUCESSO!
echo.
echo   * STS Server:   127.0.0.1:6600          (Log: logs\sts_server.log)
echo   * Auth Server:  127.0.0.1:2106 / 13001  (Log: logs\auth_server.log)
echo   * Game Server:  127.0.0.1:7777          (Log: logs\game_server.log)
echo.
echo   As janelas individuais exibem os logs em tempo real e gravam em disco.
echo   Para abrir o jogo, execute: Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
echo   Para parar os servidores, execute: deploy\PARAR_SERVIDOR.bat
echo =========================================================================
echo.
pause
