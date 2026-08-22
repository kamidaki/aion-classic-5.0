@echo off
chcp 65001 > nul
title Parar Aion Classic 4.5 - Servidor Rust
setlocal

echo.
echo =========================================================================
echo   ENCERRANDO SERVIDORES DO AION CLASSIC 4.5
echo =========================================================================
echo.

taskkill /F /IM game-server.exe 2>nul
taskkill /F /IM auth-server.exe 2>nul
taskkill /F /IM sts-server.exe 2>nul
taskkill /F /IM launcher.exe 2>nul

echo.
echo   [+] Todos os processos do servidor foram encerrados com sucesso.
echo.
timeout /t 2 > nul
