@echo off
echo Fechando o emulador e o cliente...
taskkill /F /IM Aion.bin      2>nul
taskkill /F /IM launcher.exe  2>nul
taskkill /F /IM game-server.exe 2>nul
taskkill /F /IM sts-server.exe  2>nul
taskkill /F /IM auth-server.exe 2>nul
echo Pronto.
REM ping em vez de timeout: o timeout do Windows falha com erro vermelho quando a
REM entrada esta redirecionada, e o ping espera do mesmo jeito sem depender disso.
ping -n 3 127.0.0.1 >nul
