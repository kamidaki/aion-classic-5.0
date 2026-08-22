@echo off
title Aion Classic (EU 4.5) - Iniciar Cliente
color 0b

echo ============================================================
echo      Iniciando Cliente Aion Classic EU (Gameforge x64)     
echo ============================================================
echo.

set "ROOT_DIR=%~dp0.."
set "CLIENT_DIR=%ROOT_DIR%\Cliente\GFAion\aionclassic"
set "CLIENT_BIN=%CLIENT_DIR%\bin64\aion.bin"
set "LAUNCHER_EXE=%ROOT_DIR%\deploy\launcher.exe"

if not exist "%CLIENT_BIN%" (
    echo [ERRO] Binario aion.bin nao encontrado em: %CLIENT_BIN%
    pause
    exit /b 1
)

echo Diretorio do jogo: %CLIENT_DIR%
echo Conectando ao servidor local em 127.0.0.1
echo.

cd /d "%CLIENT_DIR%"
set "AION_CLIENT=%CLIENT_BIN%"
set "AION_AUTH_IP=127.0.0.1"
set "AION_STS_IP=127.0.0.1"
set "AION_GAME_IP=127.0.0.1"

if exist "%LAUNCHER_EXE%" (
    echo [*] Iniciando via Launcher RPC com autenticacao automatica...
    start "Aion Classic Launcher RPC" "%LAUNCHER_EXE%" --auto durak
) else (
    echo [*] Iniciando binario direto com parametros Gameforge HQ...
    start "" "%CLIENT_BIN%" -lang:ENG -ip:127.0.0.1 -port:2106 -usehqserver -hqip:127.0.0.1 -hqport:13001 -np:127.0.0.1 -dwsm -pwd16 -npsa -probability -nospamcheck -noweb -nowebshop -st -dpetition -hidepromo -nosatab -nosarefund -dingameshop -disabletempbanner -disabledevaschedule -recserveridx:1 -old_charInstance
)

echo.
echo [OK] Cliente iniciado com sucesso!
ping 127.0.0.1 -n 3 >nul
