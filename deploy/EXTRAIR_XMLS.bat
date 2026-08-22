@echo off
title Aion Classic (EU 4.5) - Extrair XMLs do Cliente
color 0B

echo =========================================================================
echo    EXTRAÇÃO DE XMLS DO CLIENTE AION CLASSIC 4.5 PARA O EMULADOR RUST
echo =========================================================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\scripts\extrair_xmls_cliente.ps1"

echo.
echo Pressione qualquer tecla para fechar...
pause >nul
