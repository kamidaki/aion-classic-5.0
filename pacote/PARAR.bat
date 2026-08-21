@echo off
echo Fechando o emulador e o cliente...
taskkill /F /IM Aion.bin      2>nul
taskkill /F /IM launcher.exe  2>nul
taskkill /F /IM game-server.exe 2>nul
taskkill /F /IM sts-server.exe  2>nul
taskkill /F /IM auth-server.exe 2>nul
echo Pronto.
timeout /t 2 >nul
