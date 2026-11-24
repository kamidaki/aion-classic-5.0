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

echo [INFO] Compilando FreeType2 C units...
cl.exe /nologo /c /O2 /W3 /MD ^
    -DWIN64 -D_AMD64_ -D_WIN64 -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -DFT2_BUILD_LIBRARY ^
    -I. -ICryCommon -IFreeType2\include ^
    FreeType2\src\autohint\autohint.c ^
    FreeType2\src\base\ftbase.c ^
    FreeType2\src\base\ftbbox.c ^
    FreeType2\src\base\ftbdf.c ^
    FreeType2\src\base\ftdebug.c ^
    FreeType2\src\base\ftglyph.c ^
    FreeType2\src\base\ftinit.c ^
    FreeType2\src\base\ftmm.c ^
    FreeType2\src\base\ftpfr.c ^
    FreeType2\src\base\ftsystem.c ^
    FreeType2\src\base\ftwinfnt.c ^
    FreeType2\src\cache\ftcache.c ^
    FreeType2\src\psaux\psaux.c ^
    FreeType2\src\pshinter\pshinter.c ^
    FreeType2\src\psnames\psnames.c ^
    FreeType2\src\raster\raster.c ^
    FreeType2\src\sfnt\sfnt.c ^
    FreeType2\src\smooth\smooth.c ^
    FreeType2\src\truetype\truetype.c ^
    FreeType2\src\winfonts\winfnt.c ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao de FreeType2!
    exit /b %errorlevel%
)

echo [INFO] Compilando CryFont C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYFONT_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon -IFreeType2\include ^
    CryFont.cpp ^
    CryPakIO.cpp ^
    FBitmap.cpp ^
    FFont.cpp ^
    FFontXML.cpp ^
    FontRenderer.cpp ^
    FontTexture.cpp ^
    GlyphBitmap.cpp ^
    GlyphCache.cpp ^
    ICryFont.cpp ^
    GraphicCharInfo.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CryFont!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryFont.dll...
link.exe /nologo /DLL ^
    /DEF:CryFont.def ^
    /OUT:"%OUT_DIR%\CryFont.dll" ^
    /IMPLIB:"%OUT_DIR%\CryFont.lib" ^
    /PDB:"%OUT_DIR%\CryFont.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryFont.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryFont.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryFont.dll
echo =======================================================
