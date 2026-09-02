@echo off
title Aion Classic 5.0 - Parar Servidores
echo Encerrando processos Java do Aion Classic...
taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - LoginServer*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - GameServer*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - ChatServer*" /T >nul 2>&1
echo Servidores finalizados com sucesso
