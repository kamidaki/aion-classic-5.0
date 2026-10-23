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

echo [INFO] Compilando CryScriptSystem C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYSCRIPTSYSTEM_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon -ILUA ^
    CryScriptSystem.cpp ^
    FunctionHandler.cpp ^
    ScriptObject.cpp ^
    ScriptSystem.cpp ^
    LuaCryPakIO.cpp ^
    RecycleAllocator.cpp ^
    ScriptBuffer.cpp ^
    MemStats.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CryScriptSystem!
    exit /b %errorlevel%
)

echo [INFO] Compilando motor Lua 5.0 C units...
cl.exe /nologo /c /O2 /W3 /MD ^
    -DWIN64 -D_AMD64_ -D_WIN64 -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -I. -ICryCommon -ILUA ^
    vectorlib.c ^
    LUA\lapi.c ^
    LUA\lcode.c ^
    LUA\ldebug.c ^
    LUA\ldo.c ^
    LUA\lfunc.c ^
    LUA\lgc.c ^
    LUA\llex.c ^
    LUA\lmem.c ^
    LUA\lobject.c ^
    LUA\lopcodes.c ^
    LUA\lparser.c ^
    LUA\lstate.c ^
    LUA\lstring.c ^
    LUA\ltable.c ^
    LUA\ltm.c ^
    LUA\lundump.c ^
    LUA\lvm.c ^
    LUA\lzio.c ^
    LUA\lib\lauxlib.c ^
    LUA\lib\lbaselib.c ^
    LUA\lib\lbitlib.c ^
    LUA\lib\ldblib.c ^
    LUA\lib\liolib.c ^
    LUA\lib\lmathlib.c ^
    LUA\lib\lstrlib.c ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao Lua C!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryScriptSystem.dll...
link.exe /nologo /DLL ^
    /DEF:CryScriptSystem.def ^
    /OUT:"%OUT_DIR%\CryScriptSystem.dll" ^
    /IMPLIB:"%OUT_DIR%\CryScriptSystem.lib" ^
    /PDB:"%OUT_DIR%\CryScriptSystem.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryScriptSystem.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryScriptSystem.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryScriptSystem.dll
echo =======================================================
