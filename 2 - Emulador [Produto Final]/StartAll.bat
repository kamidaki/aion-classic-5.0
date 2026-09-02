@echo off
title Aion Classic 5.0 - Servidores
echo ===============================================================================
echo               INICIANDO AION CLASSIC 5.0 EU EMULATOR SUITE
echo ===============================================================================

echo [*] Iniciando LoginServer...
cd /d "%~dp0LoginServer"
start "Aion 5.0 - LoginServer" cmd /k "StartLS.bat"
timeout /t 2 /nobreak >nul

echo [*] Iniciando ChatServer...
cd /d "%~dp0ChatServer"
start "Aion 5.0 - ChatServer" cmd /k "StartCS.bat"
timeout /t 2 /nobreak >nul

echo [*] Iniciando GameServer...
cd /d "%~dp0GameServer"
start "Aion 5.0 - GameServer" cmd /k "StartGS.bat"

echo [OK] Todos os servidores foram iniciados em janelas separadas
