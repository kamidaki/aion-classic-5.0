@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "VS_VCVARS="

REM 1. Verificar se ja esta em ambiente de build (vswhere)
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath`) do (
        if exist "%%i\VC\Auxiliary\Build\vcvars64.bat" (
            set "VS_VCVARS=%%i\VC\Auxiliary\Build\vcvars64.bat"
        )
    )
)

REM 2. Fallbacks conhecidos para VS 2022 (Community, BuildTools, Professional, Enterprise)
if not defined VS_VCVARS (
    for %%p in (
        "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
        "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
        "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
        "%ProgramFiles%\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"
        "%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat"
    ) do (
        if exist %%p (
            set "VS_VCVARS=%%~p"
            goto :vcvars_found
        )
    )
)

:vcvars_found
if defined VS_VCVARS (
    echo [*] Inicializando ambiente MSVC: "!VS_VCVARS!"
    call "!VS_VCVARS!" >nul 2>&1
) else (
    echo [AVISO] vcvars64.bat nao encontrado explicitamente. Tentando compilacao direta via Cargo...
)

echo [*] Compilando Aion Classic - EMULADOR (Release)...
cargo build --release
if errorlevel 1 (
    echo [ERRO] Falha na compilacao de Aion Classic - EMULADOR.
    exit /b 1
)

set "DEST1=%~dp0..\..\..\Emulador - Produto Final\Aion Classic - EMULADOR.exe"
echo [*] Publicando binario em "%DEST1%"...
copy /Y "target\release\aion-classic-emu.exe" "%DEST1%" >nul

echo [OK] Aion Classic - EMULADOR.exe publicado com sucesso em "Emulador - Produto Final".



