@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

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

echo [INFO] Compilando arquivos C++...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYINPUT_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon ^
    CryInput.cpp ^
    Input.cpp ^
    XKeyboard.cpp ^
    XMouse.cpp ^
    Joystick.cpp ^
    XActionMap.cpp ^
    XActionMapManager.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryInput.dll...
link.exe /nologo /DLL ^
    /DEF:CryInput.def ^
    /OUT:"%OUT_DIR%\CryInput.dll" ^
    /IMPLIB:"%OUT_DIR%\CryInput.lib" ^
    /PDB:"%OUT_DIR%\CryInput.pdb" ^
    "%OUT_DIR%\CryInput.obj" ^
    "%OUT_DIR%\Input.obj" ^
    "%OUT_DIR%\XKeyboard.obj" ^
    "%OUT_DIR%\XMouse.obj" ^
    "%OUT_DIR%\Joystick.obj" ^
    "%OUT_DIR%\XActionMap.obj" ^
    "%OUT_DIR%\XActionMapManager.obj" ^
    User32.lib Kernel32.lib Advapi32.lib Dinput8.lib Dxguid.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryInput.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryInput.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryInput.dll
echo =======================================================
