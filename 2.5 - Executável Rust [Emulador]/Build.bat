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

echo [*] Publicando binario em '..\2 - Emulador [Produto Final]\Aion Classic - EMU.exe'...
if not exist "..\2 - Emulador [Produto Final]" mkdir "..\2 - Emulador [Produto Final]"
copy /Y "target\release\aion-classic-emu.exe" "..\2 - Emulador [Produto Final]\Aion Classic - EMU.exe" >nul

echo [OK] Aion Classic - EMU.exe publicado com sucesso em '2 - Emulador [Produto Final]'.
