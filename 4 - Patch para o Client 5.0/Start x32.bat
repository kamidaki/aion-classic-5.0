@echo off

set "ENABLE_DXVK=1"
REM =========================================================================================
REM  Aion Classic EU 5.0 (32-bit / x86) - Script de Inicializacao (Start_Classic_32.bat)
REM =========================================================================================
REM  Inicia o executavel de 32-bit do cliente (bin32\Aion.bin) com suporte total da version.dll x86.
REM =========================================================================================

start bin32\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -dss -dce
