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

echo [INFO] Compilando CryPhysics C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYPHYSICS_EXPORTS -DPHYSICS_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon ^
    aabbtree.cpp ^
    articulatedentity.cpp ^
    boolean2d.cpp ^
    boxgeom.cpp ^
    CryPhysics.cpp ^
    cylindergeom.cpp ^
    geoman.cpp ^
    geometry.cpp ^
    heightfieldbv.cpp ^
    heightfieldgeom.cpp ^
    intersectionchecks.cpp ^
    linunprojectionchecks.cpp ^
    livingentity.cpp ^
    matrixnm.cpp ^
    obbtree.cpp ^
    overlapchecks.cpp ^
    particleentity.cpp ^
    physicalentity.cpp ^
    physicalplaceholder.cpp ^
    physicalworld.cpp ^
    qhull.cpp ^
    raybv.cpp ^
    raygeom.cpp ^
    rigidbody.cpp ^
    rigidentity.cpp ^
    ropeentity.cpp ^
    rotunprojectionchecks.cpp ^
    singleboxtree.cpp ^
    softentity.cpp ^
    spheregeom.cpp ^
    trimesh.cpp ^
    utils.cpp ^
    wheeledvehicleentity.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CryPhysics!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryPhysics.dll...
link.exe /nologo /DLL ^
    /DEF:CryPhysics.def ^
    /OUT:"%OUT_DIR%\CryPhysics.dll" ^
    /IMPLIB:"%OUT_DIR%\CryPhysics.lib" ^
    /PDB:"%OUT_DIR%\CryPhysics.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryPhysics.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryPhysics.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryPhysics.dll
echo =======================================================
