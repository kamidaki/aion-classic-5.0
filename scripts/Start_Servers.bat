@echo off
title Aion Classic (EU 4.5) - Iniciar Servidores (.NET 9)
color 0a

echo ============================================================
echo      Iniciando Servidores Aion Classic EU (Gameforge)      
echo ============================================================
echo.

set LS_EXE=%~dp0src\AionClassic.LoginServer\bin\Debug\net9.0\AionClassic.LoginServer.exe
set GS_EXE=%~dp0src\AionClassic.GameServer\bin\Debug\net9.0\AionClassic.GameServer.exe

if not exist "%LS_EXE%" (
    echo Compilando servidores...
    "%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe" build "%~dp0AionClassic.sln" -c Debug
)

echo [1/2] Iniciando Login Server (Porta 2106)...
start "Aion Classic - Login Server" "%LS_EXE%"

timeout /t 2 /nobreak >nul

echo [2/2] Iniciando Game Server (Porta 7777)...
start "Aion Classic - Game Server" "%GS_EXE%"

echo.
echo ============================================================
echo   Servidores em execucao!
echo   Login Server: 127.0.0.1:2106
echo   Game Server:  127.0.0.1:7777
echo.
echo   Agora de dois cliques em: Start_Client_Classic_EU.bat
echo ============================================================
pause
