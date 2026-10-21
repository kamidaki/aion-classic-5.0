@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "DEPLOY_DIR=D:\GameForge\aionclassic\bin64"
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
rc.exe /nologo /i resources /fo "%OUT_DIR%\Game.res" resources\Game.rc
if %errorlevel% neq 0 (
    echo [ERROR] rc.exe falhou!
    exit /b %errorlevel%
)

echo [INFO] Compilando unidades modulares canonicas em %OUT_DIR%...
cl.exe /nologo /O2 /W3 /std:c++17 /EHsc /MD /LD /GR ^
    core\GameGlobals.cpp ^
    core\GameLog.cpp ^
    core\Game.cpp ^
    core\DllMain.cpp ^
    exports\GameExports.cpp ^
    net\AionClientPackets.cpp ^
    net\AionServerPackets.cpp ^
    net\ClientToServerRouter.cpp ^
    net\AionRouters.cpp ^
    ai\AIObject.cpp ^
    ai\AIToyPet.cpp ^
    ai\AiStatesExt.cpp ^
    tables\AbyssTable.cpp ^
    tables\ActionPresetTable.cpp ^
    tables\AssemblyItemTable.cpp ^
    tables\ArtiTable.cpp ^
    tables\FlyPathTable.cpp ^
    tables\GameTablesExt.cpp ^
    path\CPathFileReader.cpp ^
    path\PathSector.cpp ^
    path\SimplePathSector.cpp ^
    path\ComplexPathSector.cpp ^
    ui\AddonFrame.cpp ^
    ui\AddonBrowser.cpp ^
    ui\AddonButton.cpp ^
    ui\AddonContainer.cpp ^
    ui\AddonGauge.cpp ^
    ui\AddonWidgets.cpp ^
    ui\AddonExt.cpp ^
    ui\GameDialogsExt.cpp ^
    game\Player.cpp ^
    game\Items.cpp ^
    game\EngineObjects.cpp ^
    game\GameplayExt.cpp ^
    game\CombatMath.cpp ^
    /Fo"%OUT_DIR%\\" ^
    /link ^
    /DEF:Game.def ^
    /OUT:"%OUT_DIR%\Game.dll" ^
    /IMPLIB:"%OUT_DIR%\Game.lib" ^
    /PDB:"%OUT_DIR%\Game.pdb" ^
    "%OUT_DIR%\Game.res" ^
    User32.lib Kernel32.lib Advapi32.lib Gdi32.lib Ws2_32.lib

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao ou linkedicao!
    exit /b %errorlevel%
)

echo.
echo =======================================================
echo [INFO] Validando exportacoes PE com dumpbin...
echo =======================================================
dumpbin /exports "%OUT_DIR%\Game.dll"

echo.
echo =======================================================
echo [SUCESSO] Game.dll Classic 5.0 compilada com ZERO erros em %OUT_DIR%\Game.dll
echo =======================================================

if "%1"=="deploy" (
    echo [INFO] Solicitado deploy para %DEPLOY_DIR%...
    if exist "%DEPLOY_DIR%\Game.dll" (
        if not exist "%DEPLOY_DIR%\Game.dll.original.bak" (
            echo [INFO] Criando backup de seguranca do Game.dll original em Game.dll.original.bak...
            copy /Y "%DEPLOY_DIR%\Game.dll" "%DEPLOY_DIR%\Game.dll.original.bak"
        )
    )
    copy /Y "%OUT_DIR%\Game.dll" "%DEPLOY_DIR%\Game.dll"
    echo [INFO] Deploy concluido com sucesso!
) else (
    echo [NOTA] Binario gerado em '%OUT_DIR%\Game.dll'.
    echo [NOTA] Para fazer deploy para o cliente Aion Classic substituindo com backup, execute:
    echo        Build64.bat deploy
)

exit /b 0
