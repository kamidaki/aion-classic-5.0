@echo off
cd /d G:\CodexHELPER\ClaudeAion\aion-main

echo Iniciando servidores Aion...

echo Matando processos anteriores...
taskkill /F /IM gfclient.exe 2>nul
taskkill /F /IM AION.bin 2>nul
taskkill /F /IM auth-server.exe 2>nul
taskkill /F /IM sts-server.exe 2>nul
taskkill /F /IM game-server.exe 2>nul

set AION_GAME_IP=192.168.100.77
start "Auth Server"  cmd /k "cargo run -p auth-server"
start "STS Server"   cmd /k "cargo run -p sts-server"
start "Game Server"  cmd /k "cargo run -p game-server"

echo.
echo Aguardando servidores iniciarem...
timeout /t 5 /nobreak >nul

start "Launcher"     cmd /k "cargo run -p launcher -- --auto dev"