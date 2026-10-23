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

echo [INFO] Compilando Cry3DEngine C++ units...
cl.exe /nologo /c /O2 /W3 /std:c++17 /EHsc /MD /GR ^
    -DWIN64 -D_AMD64_ -D_WIN64 -DCRY3DENGINE_EXPORTS -D_CRT_SECURE_NO_WARNINGS -D_CRT_NONSTDC_NO_DEPRECATE ^
    -D_ENFORCE_MATCHING_ALLOCATORS=0 -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS ^
    -I. -ICryCommon ^
    3DEngineLight.cpp ^
    3DEngineRender.cpp ^
    3DEngineScreenEffects.cpp ^
    3dEngine.cpp ^
    3dEngineLoad.cpp ^
    Aion3DEngineBinds.cpp ^
    BasicArea.cpp ^
    Brush.cpp ^
    BrushLM.cpp ^
    Cry3DEngine.cpp ^
    CryStaticModel.cpp ^
    Decal.cpp ^
    DecalManager.cpp ^
    File.cpp ^
    Geom.cpp ^
    Helper.cpp ^
    LMSerializationManager2.cpp ^
    Light.cpp ^
    LightLoad.cpp ^
    LightMan.cpp ^
    MatMan.cpp ^
    Meshidx.cpp ^
    Node.cpp ^
    ObjMan.cpp ^
    ObjManDraw.cpp ^
    ObjManDrawEntity.cpp ^
    ObjManFar.cpp ^
    ObjManPhys.cpp ^
    ObjManShadows.cpp ^
    ObjManStreaming.cpp ^
    ParticleEffect.cpp ^
    ParticleEmitter.cpp ^
    SaveCFG.cpp ^
    SpriteManager.cpp ^
    StatObjCompiler.cpp ^
    StatObjConstr.cpp ^
    StatObjFar.cpp ^
    StatObjLoad.cpp ^
    StatObjPhys.cpp ^
    StatObjRend.cpp ^
    StatObjSerialize.cpp ^
    StatObjShadow.cpp ^
    StatObjShadowVolumes.cpp ^
    StatObjStream.cpp ^
    StdAfx.cpp ^
    StencilShadowConnectivityBuilder.cpp ^
    StencilShadowEdgeDetector.cpp ^
    Vegetation.cpp ^
    VisAreaMan.cpp ^
    VisAreas.cpp ^
    WaterVolumes.cpp ^
    bflyes.cpp ^
    cbuffer.cpp ^
    cvars.cpp ^
    detail_grass.cpp ^
    particle.cpp ^
    partman.cpp ^
    partpolygon.cpp ^
    rain.cpp ^
    terrain.cpp ^
    terrain_damage.cpp ^
    terrain_det_tex.cpp ^
    terrain_hmap.cpp ^
    terrain_init.cpp ^
    terrain_light.cpp ^
    terrain_load.cpp ^
    terrain_render.cpp ^
    terrain_sector.cpp ^
    terrain_sector_beach.cpp ^
    terrain_sector_render.cpp ^
    terrain_sector_tex.cpp ^
    terrain_tex_pool.cpp ^
    terrain_water_quad.cpp ^
    terran_edit.cpp ^
    /Fo"%OUT_DIR%\\"

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao C++ de Cry3DEngine!
    exit /b %errorlevel%
)

echo [INFO] Linkando Cry3DEngine.dll...
link.exe /nologo /DLL ^
    /DEF:Cry3DEngine.def ^
    /OUT:"%OUT_DIR%\Cry3DEngine.dll" ^
    /IMPLIB:"%OUT_DIR%\Cry3DEngine.lib" ^
    /PDB:"%OUT_DIR%\Cry3DEngine.pdb" ^
    "%OUT_DIR%\*.obj" ^
    User32.lib Kernel32.lib Advapi32.lib Winmm.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na linkagem de Cry3DEngine.dll!
    exit /b %errorlevel%
)

echo =======================================================
echo [SUCESSO] Cry3DEngine.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\Cry3DEngine.dll
echo =======================================================
