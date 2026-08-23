@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo   INICIANDO CLIENTE AION CLASSIC EU (GAMEFORGE / EMURUST)
echo =========================================================================

set "CLIENT_BIN=bin64\Aion.bin"

if not exist "%CLIENT_BIN%" (
    echo [ERRO] Executavel %CLIENT_BIN% nao encontrado!
    pause
    exit /b 1
)

echo [*] Iniciando cliente Aion Classic 64-bit...
start "" "%CLIENT_BIN%" -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -loginex

echo [OK] Cliente iniciado com sucesso.
