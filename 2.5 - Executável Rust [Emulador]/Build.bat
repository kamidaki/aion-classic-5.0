@echo off
setlocal

set "VS_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VS_VCVARS%" (
    echo [ERRO] Visual Studio 2022 Community nao encontrado em %VS_VCVARS%
    exit /b 1
)

echo [*] Inicializando ambiente MSVC...
call "%VS_VCVARS%" >nul 2>&1

echo [*] Compilando Aion Classic - EMU (Release)...
cargo build --release
if errorlevel 1 (
    echo [ERRO] Falha na compilacao de Aion Classic - EMU.
    exit /b 1
)

set "DEST=D:\AION CLASSIC 5.0 - BEYOND TESTE\EMULADOR FINAL\Aion Classic - EMU.exe"
echo [*] Publicando binario em "%DEST%"...
copy /Y "target\release\aion-classic-emu.exe" "%DEST%" >nul

echo [OK] Aion Classic - EMU.exe publicado com sucesso em EMULADOR FINAL.

