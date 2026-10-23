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

echo [INFO] Compilando CryAnimation C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRYANIMATION_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon ^
    AnimObject.cpp ^
    AnimObjectLoader.cpp ^
    AnimObjectManager.cpp ^
    BoneLightBindInfo.cpp ^
    BoneLightDynamicBind.cpp ^
    BSplineKnots.cpp ^
    BSplineOpen.cpp ^
    BSplineVec3dPacked.cpp ^
    CgfUtils.cpp ^
    ChunkFileReader.cpp ^
    Controller.cpp ^
    ControllerCryBone.cpp ^
    ControllerManager.cpp ^
    ControllerPackedBSpline.cpp ^
    ControllerTCB.cpp ^
    CryAnimationBase.cpp ^
    CryBone.cpp ^
    CryBoneDesc.cpp ^
    CryBoneHierarchyLoader.cpp ^
    CryBoneInfo.cpp ^
    CryCharBody.cpp ^
    CryCharDecal.cpp ^
    CryCharDecalBuilder.cpp ^
    CryCharDecalManager.cpp ^
    CryCharFxTrail.cpp ^
    CryCharInstance.cpp ^
    CryCharInstanceRenderParams.cpp ^
    CryCharManager.cpp ^
    CryCharParticleManager.cpp ^
    CryCharRenderElement.cpp ^
    CryCharReShadowManager.cpp ^
    CryCharReShadowVolume.cpp ^
    CryGeometryInfo.cpp ^
    CryGeomMorphTarget.cpp ^
    CryKeyInterpolation.cpp ^
    CryModEffAnimation.cpp ^
    CryModEffIKSolver.cpp ^
    CryModEffMorph.cpp ^
    CryModel-Data.cpp ^
    CryModel.cpp ^
    CryModelAnimationContainer.cpp ^
    CryModelArrays.cpp ^
    CryModelGeometryLoader.cpp ^
    CryModelLoader.cpp ^
    CryModelShadowVolume.cpp ^
    CryModelState.cpp ^
    CryModelStatePhys.cpp ^
    CryModelSubmesh.cpp ^
    CrySkinBase.cpp ^
    CrySkinBasisBuilder.cpp ^
    CrySkinBuilder.cpp ^
    CrySkinBuilderBase.cpp ^
    CrySkinFull.cpp ^
    CrySkinMorph.cpp ^
    CrySkinMorphBuilder.cpp ^
    CrySkinRigidBasis.cpp ^
    CryVertexBinding.cpp ^
    cvars.cpp ^
    DebugUtils.cpp ^
    drand.cpp ^
    FileMapping.cpp ^
    IncContHeap.cpp ^
    makepath.cpp ^
    MathUtils.cpp ^
    QuaternionExponentX87.cpp ^
    RenderUtils.cpp ^
    splitpath.cpp ^
    SSEUtils.cpp ^
    VertexBufferArrayDrivers.cpp ^
    AionAnimationBinds.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de CryAnimation!
    exit /b %errorlevel%
)

echo [INFO] Montando CrySkinAMD64.asm...
ml64.exe /nologo /c /Fo"%OUT_DIR%\CrySkinAMD64.obj" CrySkinAMD64.asm
if %errorlevel% neq 0 (
    echo [ERROR] Falha ao montar CrySkinAMD64.asm!
    exit /b %errorlevel%
)

echo [INFO] Linkando CryAnimation.dll...
link.exe /nologo /DLL ^
    /DEF:CryAnimation.def ^
    /OUT:"%OUT_DIR%\CryAnimation.dll" ^
    /IMPLIB:"%OUT_DIR%\CryAnimation.lib" ^
    /PDB:"%OUT_DIR%\CryAnimation.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de CryAnimation.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] CryAnimation.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\CryAnimation.dll
echo =======================================================
