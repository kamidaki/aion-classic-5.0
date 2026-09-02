@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo   COMPILADOR AUTOMATIZADO - AION VERSION.DLL (32-BIT e 64-BIT)
echo =========================================================================

set "VS_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
set "SLN_PATH=src\AionVersionDll.sln"
if not defined CLIENT_DIR (
    if exist "..\..\GameForge\aionclassic" (
        set "CLIENT_DIR=..\..\GameForge\aionclassic"
    ) else (
        set "CLIENT_DIR="
    )
)
set "PATCH_DIR=..\4 - Patch para o Client 5.0"

if not exist "%VS_VCVARS%" (
    echo [ERRO] Visual Studio 2022 Developer Tools nao encontrado em %VS_VCVARS%
    pause
    exit /b 1
)

echo [*] Inicializando ambiente MSVC...
call "%VS_VCVARS%" >nul 2>&1

echo [*] Restaurando pacotes NuGet (Detours)...
if not exist "nuget.exe" (
    powershell -Command "Invoke-WebRequest -Uri 'https://dist.nuget.org/win-x86-commandline/latest/nuget.exe' -OutFile 'nuget.exe'"
)
nuget.exe restore "%SLN_PATH%" >nul 2>&1

echo [*] Compilando version.dll (x64 Release)...
msbuild "%SLN_PATH%" -p:Configuration=Release -p:Platform=x64 -p:PlatformToolset=v143 -v:m -nologo
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha na compilacao da versao x64!
    pause
    exit /b 1
)

echo [*] Compilando version.dll (x86 Release)...
msbuild "%SLN_PATH%" -p:Configuration=Release -p:Platform=x86 -p:PlatformToolset=v143 -v:m -nologo
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha na compilacao da versao x86!
    pause
    exit /b 1
)

echo [*] Copiando binarios para Client Patch e Pasta Real 5.0 (%CLIENT_DIR%)...

if exist "src\x64\Release\version.dll" (
    if not exist "%PATCH_DIR%\bin64" mkdir "%PATCH_DIR%\bin64"
    copy /y "src\x64\Release\version.dll" "%PATCH_DIR%\bin64\version.dll" >nul
    if exist "%CLIENT_DIR%\bin64" (
        copy /y "src\x64\Release\version.dll" "%CLIENT_DIR%\bin64\version.dll" >nul
        echo   [OK] bin64\version.dll ^(x64^) copiado para Client Patch e Jogo Real 5.0!
    )
)

if exist "src\Release\version.dll" (
    if not exist "%PATCH_DIR%\bin32" mkdir "%PATCH_DIR%\bin32"
    copy /y "src\Release\version.dll" "%PATCH_DIR%\bin32\version.dll" >nul
    if exist "%CLIENT_DIR%\bin32" (
        copy /y "src\Release\version.dll" "%CLIENT_DIR%\bin32\version.dll" >nul
        echo   [OK] bin32\version.dll ^(x86^) copiado para Client Patch e Jogo Real 5.0!
    )
)

if exist "lib\dxvk\x64\d3d9.dll" (
    copy /y "lib\dxvk\x64\d3d9.dll" "%PATCH_DIR%\bin64\d3d9.dll" >nul
    if exist "%CLIENT_DIR%\bin64" (
        copy /y "lib\dxvk\x64\d3d9.dll" "%CLIENT_DIR%\bin64\d3d9.dll" >nul
        echo   [OK] bin64\d3d9.dll ^(DXVK Sarek Vulkan^) instalado em Client Patch e Jogo Real 5.0!
    )
)

if exist "lib\dxvk\x32\d3d9.dll" (
    copy /y "lib\dxvk\x32\d3d9.dll" "%PATCH_DIR%\bin32\d3d9.dll" >nul
    if exist "%CLIENT_DIR%\bin32" (
        copy /y "lib\dxvk\x32\d3d9.dll" "%CLIENT_DIR%\bin32\d3d9.dll" >nul
        echo   [OK] bin32\d3d9.dll ^(DXVK Sarek Vulkan^) instalado em Client Patch e Jogo Real 5.0!
    )
)

if exist "%PATCH_DIR%\Start_Classic.bat" (
    if exist "%CLIENT_DIR%" (
        copy /y "%PATCH_DIR%\Start_Classic.bat" "%CLIENT_DIR%\Start_Classic.bat" >nul
        echo   [OK] Start_Classic.bat sincronizado no cliente 5.0!
    )
)

if exist "%PATCH_DIR%\Start_Classic_32.bat" (
    if exist "%CLIENT_DIR%" (
        copy /y "%PATCH_DIR%\Start_Classic_32.bat" "%CLIENT_DIR%\Start_Classic_32.bat" >nul
        echo   [OK] Start_Classic_32.bat sincronizado no cliente 5.0!
    )
)

echo =========================================================================
echo   BUILD E DEPLOY 5.0 CONCLUIDO COM SUCESSO!
echo =========================================================================
