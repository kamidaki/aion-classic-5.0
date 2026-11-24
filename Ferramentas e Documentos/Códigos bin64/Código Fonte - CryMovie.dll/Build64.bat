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

echo [INFO] Compilando CryMovie C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYMOVIE_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon ^
    AnimCameraNode.cpp ^
    AnimNode.cpp ^
    AnimSequence.cpp ^
    AnimSplineTrack.cpp ^
    AnimTrack.cpp ^
    BoolTrack.cpp ^
    CharacterTrack.cpp ^
    ConsoleTrack.cpp ^
    CryMovie.cpp ^
    CVarNode.cpp ^
    EntityNode.cpp ^
    EventTrack.cpp ^
    ExprTrack.cpp ^
    MaterialNode.cpp ^
    Movie.cpp ^
    MusicTrack.cpp ^
    SceneNode.cpp ^
    ScriptVarNode.cpp ^
    SelectTrack.cpp ^
    SequenceIt.cpp ^
    SoundTrack.cpp ^
    AionMovieTracks.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CryMovie!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryMovie.dll...
link.exe /nologo /DLL ^
    /DEF:CryMovie.def ^
    /OUT:"%OUT_DIR%\CryMovie.dll" ^
    /IMPLIB:"%OUT_DIR%\CryMovie.lib" ^
    /PDB:"%OUT_DIR%\CryMovie.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryMovie.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryMovie.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryMovie.dll
echo =======================================================
