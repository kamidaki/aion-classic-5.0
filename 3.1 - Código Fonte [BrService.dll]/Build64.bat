@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo =========================================================================
echo   COMPILADOR AUTOMATIZADO - AION BRSERVICE.DLL (64-BIT)
echo =========================================================================

set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not exist "%VCVARS%" (
    echo [ERRO] Visual Studio 2022 vcvarsall.bat nao encontrado em %VCVARS%
    pause
    exit /b 1
)

echo [*] Inicializando ambiente MSVC x64...
call "%VCVARS%" x64 >nul 2>&1

if not exist "x64\Release" mkdir "x64\Release"
del /Q "x64\Release\*.obj" 2>nul

echo [*] Compilando motor SQLite3...
cl /c /O2 /utf-8 /W3 /D NDEBUG /D _WINDOWS /D _USRDLL /D SQLITE_THREADSAFE=1 /D SQLITE_ENABLE_FTS5 /MD /EHsc /Fox64\Release\ database\sqlite3.c
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha na compilacao do SQLite3!
    exit /b 1
)

echo [*] Compilando modulos C++ (BrService.dll)...
cl /c /O2 /utf-8 /W3 /std:c++17 /EHsc /MD /D NDEBUG /D _WINDOWS /D _USRDLL /D _UNICODE /D UNICODE /D NOMINMAX /D _WINSOCK_DEPRECATED_NO_WARNINGS /I. /Idatabase /Icore /Fox64\Release\ ^
    core\ServiceGlobals.cpp ^
    core\ServiceLog.cpp ^
    core\ServiceWorker.cpp ^
    config\BrConfig.cpp ^
    cvar\CVarManager.cpp ^
    network\PingEngine.cpp ^
    network\WebSocketClient.cpp ^
    database\CombatDb.cpp ^
    model3d\CryModelBridge.cpp ^
    ui\UICommon.cpp ^
    ui\PingHudUI.cpp ^
    ui\DrawerModalUI.cpp ^
    core\DllMain.cpp
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha na compilacao dos fontes C++!
    exit /b 1
)

echo [*] Linkando BrService.dll (x64)...
link /NOLOGO /DLL /OUT:x64\Release\BrService.dll /DEF:BrService.def x64\Release\*.obj user32.lib gdi32.lib gdiplus.lib ws2_32.lib iphlpapi.lib shell32.lib ole32.lib dwmapi.lib
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha na linkagem da BrService.dll!
    exit /b 1
)

set "PATCH_DIR=..\4 - Patch para o Client 5.0"
set "CLIENT_DIR=..\..\GameForge\aionclassic"

echo [*] Publicando BrService.dll...
if exist "x64\Release\BrService.dll" (
    if not exist "%PATCH_DIR%\bin64" mkdir "%PATCH_DIR%\bin64"
    copy /y "x64\Release\BrService.dll" "%PATCH_DIR%\bin64\BrService.dll" >nul
    echo   [OK] bin64\BrService.dll copiado para Client Patch 5.0.

    if exist "%CLIENT_DIR%\bin64" (
        copy /y "x64\Release\BrService.dll" "%CLIENT_DIR%\bin64\BrService.dll" >nul
        echo   [OK] bin64\BrService.dll copiado para Jogo Real 5.0: %CLIENT_DIR%
    )
)

echo =========================================================================
echo   BUILD E DEPLOY DO BRSERVICE.DLL CONCLUIDO COM SUCESSO.
echo =========================================================================
