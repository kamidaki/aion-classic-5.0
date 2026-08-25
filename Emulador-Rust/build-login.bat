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

echo [OK] login-server compilado com sucesso.
echo [*] Copiando binario para Produto Final...
copy /Y "target\release\login-server.exe" "..\Produto Final\login-server.exe"
echo [OK] Produto Final\login-server.exe atualizado.
