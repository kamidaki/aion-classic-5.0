@echo off
title Aion Classic - Packet Sniffer & MITM Proxy (.NET 9)
color 0e

echo ============================================================
echo   Iniciando Aion Classic Packet Sniffer ^& MITM Proxy
echo ============================================================
echo.

set DOTNET_EXE=%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe
if not exist "%DOTNET_EXE%" (
    set DOTNET_EXE=dotnet
)

"%DOTNET_EXE%" run --project "%~dp0src\AionClassic.Sniffer" %*

pause
