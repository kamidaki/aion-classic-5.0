@echo off
chcp 65001 > nul
title Parar Aion Classic 4.5 - Servidor Rust
color 0c

echo.
echo =========================================================================
echo   ENCERRANDO TODOS OS SERVIDORES DO AION CLASSIC 4.5
echo =========================================================================
echo.

echo [*] Encerrando processos de servidores Rust...
taskkill /F /IM game-server.exe 2>nul
taskkill /F /IM auth-server.exe 2>nul
taskkill /F /IM sts-server.exe 2>nul

echo.
echo   [+] Todos os processos do servidor foram encerrados com sucesso!
echo.
ping 127.0.0.1 -n 3 >nul
