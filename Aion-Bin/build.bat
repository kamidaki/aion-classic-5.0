@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo   COMPILADOR AUTOMATIZADO - AION VERSION.DLL (32-BIT e 64-BIT)
echo =========================================================================

set "VS_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
set "SLN_PATH=src\AionVersionDll.sln"
set "CLIENT_DIR=..\Cliente\GFAion\aionclassic"

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

echo [*] Copiando binarios para a pasta do cliente...
if exist "src\x64\Release\version.dll" (
    copy /y "src\x64\Release\version.dll" "%CLIENT_DIR%\bin64\version.dll"
    echo   [OK] bin64\version.dll atualizado com sucesso!
)

if exist "src\Release\version.dll" (
    copy /y "src\Release\version.dll" "%CLIENT_DIR%\bin32\version.dll"
    echo   [OK] bin32\version.dll atualizado com sucesso!
)

if exist "lib\dxvk\x64\d3d9.dll" (
    copy /y "lib\dxvk\x64\d3d9.dll" "%CLIENT_DIR%\bin64\d3d9.dll"
    echo   [OK] bin64\d3d9.dll (DXVK Sarek Vulkan) instalado com sucesso!
)

if exist "lib\dxvk\x32\d3d9.dll" (
    copy /y "lib\dxvk\x32\d3d9.dll" "%CLIENT_DIR%\bin32\d3d9.dll"
    echo   [OK] bin32\d3d9.dll (DXVK Sarek Vulkan) instalado com sucesso!
)

echo =========================================================================
echo   BUILD E DEPLOY CONCLUIDO COM SUCESSO!
echo =========================================================================
