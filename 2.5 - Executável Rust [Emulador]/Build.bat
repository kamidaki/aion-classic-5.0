@echo off
setlocal

set "VS_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VS_VCVARS%" (
    echo [ERRO] Visual Studio 2022 Community nao encontrado em %VS_VCVARS%
    exit /b 1
)

echo [*] Inicializando ambiente MSVC...
call "%VS_VCVARS%" >nul 2>&1

echo [*] Compilando login-server (Release)...
cargo build --release -p login-server
if errorlevel 1 (
    echo [ERRO] Falha na compilacao do login-server.
    exit /b 1
)

echo [*] Compilando game-server (Release)...
cargo build --release -p game-server
if errorlevel 1 (
    echo [ERRO] Falha na compilacao do game-server.
    exit /b 1
)

echo [*] Compilando chat-server (Release)...
cargo build --release -p chat-server
if errorlevel 1 (
    echo [ERRO] Falha na compilacao do chat-server.
    exit /b 1
)

echo [*] Compilando auto-start (Release)...
cargo build --release -p auto-start
if errorlevel 1 (
    echo [ERRO] Falha na compilacao do auto-start.
    exit /b 1
)

echo [*] Publicando binarios em '2 - Emulador [Produto Final]'...
if not exist "..\2 - Emulador [Produto Final]" mkdir "..\2 - Emulador [Produto Final]"
copy /Y "target\release\login-server.exe" "..\2 - Emulador [Produto Final]\" >nul
copy /Y "target\release\game-server.exe" "..\2 - Emulador [Produto Final]\" >nul
copy /Y "target\release\chat-server.exe" "..\2 - Emulador [Produto Final]\" >nul
copy /Y "target\release\auto-start.exe" "..\2 - Emulador [Produto Final]\" >nul

echo [*] Compilando version.dll para o Client Patch...
pushd "..\3 - Código Fonte [Version.dll]"
call build.bat >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Falha ao compilar version.dll - verifique 3 - Código Fonte [Version.dll] manualmente.
) else (
    echo [OK] version.dll compilada. Copiando para Client Patch...
    if exist "src\x64\Release\version.dll" (
        copy /Y "src\x64\Release\version.dll" "..\4 - Patch para o Client 5.0\bin64\version.dll" >nul
        echo   [OK] 4 - Patch para o Client 5.0\bin64\version.dll atualizado.
    )
    if exist "src\Release\version.dll" (
        copy /Y "src\Release\version.dll" "..\4 - Patch para o Client 5.0\bin32\version.dll" >nul
        echo   [OK] 4 - Patch para o Client 5.0\bin32\version.dll atualizado.
    )
)
popd

echo [OK] Todos os servidores compilados e publicados com sucesso em '2 - Emulador [Produto Final]'.

