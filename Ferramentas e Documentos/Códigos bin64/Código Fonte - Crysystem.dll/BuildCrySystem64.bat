@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if defined AION_CLIENT_DIR (
    set "DEPLOY_DIR=%AION_CLIENT_DIR%\bin64"
) else (
    set "DEPLOY_DIR="
)
set "OUT_DIR=Release64"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"

if not exist "%VCVARS%" (
    echo [ERROR] Visual Studio 2022 vcvarsall.bat nao encontrado em "%VCVARS%"
    exit /b 1
)

echo =======================================================
echo [INFO] Inicializando Ambiente MSVC x64 Developer...
echo =======================================================
call "%VCVARS%" x64 > nul
if %errorlevel% neq 0 (
    echo [ERROR] Falha ao inicializar o ambiente MSVC x64.
    exit /b %errorlevel%
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo [INFO] Compilando recursos Win32...
rc.exe /nologo /i resources /fo "%OUT_DIR%\CrySystem.res" resources\CrySystem.rc
if %errorlevel% neq 0 (
    echo [ERROR] rc.exe falhou!
    exit /b %errorlevel%
)

echo [INFO] Compilando CrySystem.dll modular units...
cl.exe /nologo /O2 /W3 /std:c++17 /EHsc /MD /LD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYSYSTEM_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon -Incsoft ^
    ncsoft\GameFixedFrame.cpp ^
    ncsoft\GameOptions.cpp ^
    ncsoft\CharacterLODManager.cpp ^
    ncsoft\LITELauncherManager.cpp ^
    ncsoft\SdoaLogin.cpp ^
    ncsoft\CryFileMonitor.cpp ^
    ncsoft\CCVarSaveDump.cpp ^
    ncsoft\CCalcUnit.cpp ^
    ncsoft\CPrefetchFile.cpp ^
    ncsoft\CCheckSystemHardware.cpp ^
    AionSystemExports.cpp ^
    AionSystemCore.cpp ^
    DllMain.cpp ^
    /Fo"%OUT_DIR%\\" ^
    /link ^
    /DEF:CrySystem.def ^
    /OUT:"%OUT_DIR%\CrySystem.dll" ^
    /IMPLIB:"%OUT_DIR%\CrySystem.lib" ^
    /PDB:"%OUT_DIR%\CrySystem.pdb" ^
    "%OUT_DIR%\CrySystem.res" ^
    User32.lib Kernel32.lib Advapi32.lib Gdi32.lib Ws2_32.lib Winmm.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao ou linkedicao!
    exit /b %errorlevel%
)

echo.
echo =======================================================
echo [INFO] Validando exportacoes PE com dumpbin...
echo =======================================================
dumpbin /exports "%OUT_DIR%\CrySystem.dll"

echo.
echo =======================================================
echo [SUCESSO] CrySystem.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CrySystem.dll
echo =======================================================

if "%1"=="deploy" (
    if "%DEPLOY_DIR%"=="" (
        echo [ERROR] Defina a variavel de ambiente AION_CLIENT_DIR antes de usar deploy.
        exit /b 1
    )
    echo [INFO] Solicitado deploy para %DEPLOY_DIR%...
    if exist "%DEPLOY_DIR%\CrySystem.dll" (
        if not exist "%DEPLOY_DIR%\CrySystem.dll.original.bak" (
            echo [INFO] Criando backup de seguranca do CrySystem.dll original em CrySystem.dll.original.bak...
            copy /y "%DEPLOY_DIR%\CrySystem.dll" "%DEPLOY_DIR%\CrySystem.dll.original.bak" > nul
        )
    )
    copy /y "%OUT_DIR%\CrySystem.dll" "%DEPLOY_DIR%\CrySystem.dll"
    if %errorlevel% equ 0 (
        echo [SUCESSO] CrySystem.dll implantada com sucesso em %DEPLOY_DIR%\CrySystem.dll
    ) else (
        echo [ERROR] Falha ao copiar CrySystem.dll para %DEPLOY_DIR%
        exit /b 1
    )
)
