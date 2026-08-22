@echo off
title Aion Classic (EU 4.5) - Iniciar Cliente
color 0b

echo ============================================================
echo      Iniciando Cliente Aion Classic EU (Gameforge x64)     
echo ============================================================
echo.

set AION_DIR=D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic
set CLIENT_EXE=%AION_DIR%\bin64\Aion.exe
set CLIENT_BIN=%AION_DIR%\bin64\Aion.bin

if not exist "%AION_DIR%" (
    echo [ERRO] Pasta do Aion Classic nao encontrada em: %AION_DIR%
    pause
    exit /b 1
)

if not exist "%CLIENT_EXE%" (
    echo Criando Aion.exe a partir de Aion.bin...
    copy /y "%CLIENT_BIN%" "%CLIENT_EXE%" >nul
)

echo Diretorio do jogo: %AION_DIR%
echo Conectando ao servidor local: 127.0.0.1:2106 ...
echo.

cd /d "%AION_DIR%"

start "" "%CLIENT_EXE%" -ip:127.0.0.1 -port:2106 -cc:2 -lang:eng -account:durak -password:durak -noweb -noauthgg -nowebshop -nowebadpopup -webfin -ls -charencrypt

echo [OK] Cliente iniciado!
