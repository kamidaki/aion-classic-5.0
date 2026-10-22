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

echo [INFO] Compilando CrySoundSystem C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYSOUNDSYSTEM_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon -IOggVorbisInclude ^
    ADPCMDecoder.cpp ^
    CrySoundSystem.cpp ^
    MusicPattern.cpp ^
    MusicPatternInstance.cpp ^
    MusicSystem.cpp ^
    OGGDecoder.cpp ^
    PCMDecoder.cpp ^
    RandGen.cpp ^
    Sound.cpp ^
    SoundBuffer.cpp ^
    SoundSystem.cpp ^
    SoundSystemCommon.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CrySoundSystem!
    exit /b %errorlevel%
)

echo [INFO] Linkando CrySoundSystem.dll...
link.exe /nologo /DLL ^
    /DEF:CrySoundSystem.def ^
    /OUT:"%OUT_DIR%\CrySoundSystem.dll" ^
    /IMPLIB:"%OUT_DIR%\CrySoundSystem.lib" ^
    /PDB:"%OUT_DIR%\CrySoundSystem.pdb" ^
    "%OUT_DIR%\*.obj" ^
    crysound64.lib ogg_static_r64.lib vorbis_static_r64.lib vorbisfile_static_r64.lib ^
    legacy_stdio_definitions.lib User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CrySoundSystem.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CrySoundSystem.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CrySoundSystem.dll
echo =======================================================
