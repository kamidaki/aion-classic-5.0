@echo off
setlocal enabledelayedexpansion
title Aion Classic 5.0 EU - Build & Publish Server

echo ===============================================================================
echo                AION CLASSIC 5.0 EU - BUILD & PUBLISH PIPELINE
echo ===============================================================================
echo.

REM --- 1. Configurar JAVA_HOME para JDK 8 ---
if exist "C:\Program Files\Java\jdk1.8.0_431" (
    set "JAVA_HOME=C:\Program Files\Java\jdk1.8.0_431"
) else if not defined JAVA_HOME (
    echo [AVISO] JAVA_HOME nao definido. Tentando usar Java padrao do sistema...
)

echo [*] JAVA_HOME configurado para: %JAVA_HOME%
echo.

REM --- 2. Executar Maven Clean Package ---
echo [*] Executando Maven Build (clean package)...
call mvn clean package -DskipTests=true
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha na compilacao Maven! Verifique os logs acima.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [*] Maven Build concluido com sucesso!
echo.

REM --- 3. Preparar Diretorio de Publicacao em 2 - Emulador [Produto Final] ---
set "ROOT_DIR=%~dp0"
set "DEST_DIR=%ROOT_DIR%..\2 - Emulador [Produto Final]"

echo [*] Publicando artefatos em: %DEST_DIR%

if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"
if not exist "%DEST_DIR%\LoginServer" mkdir "%DEST_DIR%\LoginServer"
if not exist "%DEST_DIR%\GameServer" mkdir "%DEST_DIR%\GameServer"
if not exist "%DEST_DIR%\ChatServer" mkdir "%DEST_DIR%\ChatServer"
if not exist "%DEST_DIR%\LoginServer\libs" mkdir "%DEST_DIR%\LoginServer\libs"
if not exist "%DEST_DIR%\GameServer\libs" mkdir "%DEST_DIR%\GameServer\libs"
if not exist "%DEST_DIR%\ChatServer\libs" mkdir "%DEST_DIR%\ChatServer\libs"

REM --- 4. Extrair e Publicar os Servidores ---
echo [*] Publicando LoginServer...
if exist "%ROOT_DIR%LoginServer\target\LoginServer.zip" (
    powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%LoginServer\target\LoginServer.zip' -DestinationPath '%DEST_DIR%\LoginServer' -Force"
)
if exist "%ROOT_DIR%LoginServer\target\LoginServer-ClassicEmu-Brasil.jar" (
    copy /Y "%ROOT_DIR%LoginServer\target\LoginServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\LoginServer\" >nul
    copy /Y "%ROOT_DIR%LoginServer\target\LoginServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\LoginServer\libs\" >nul
)

echo [*] Publicando GameServer...
if exist "%ROOT_DIR%GameServer\target\GameServer.zip" (
    powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%GameServer\target\GameServer.zip' -DestinationPath '%DEST_DIR%\GameServer' -Force"
)
if exist "%ROOT_DIR%GameServer\target\GameServer-ClassicEmu-Brasil.jar" (
    copy /Y "%ROOT_DIR%GameServer\target\GameServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\GameServer\" >nul
    copy /Y "%ROOT_DIR%GameServer\target\GameServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\GameServer\libs\" >nul
)

echo [*] Publicando ChatServer...
if exist "%ROOT_DIR%ChatServer\target\ChatServer.zip" (
    powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%ChatServer\target\ChatServer.zip' -DestinationPath '%DEST_DIR%\ChatServer' -Force"
)
if exist "%ROOT_DIR%ChatServer\target\ChatServer-ClassicEmu-Brasil.jar" (
    copy /Y "%ROOT_DIR%ChatServer\target\ChatServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\ChatServer\" >nul
    copy /Y "%ROOT_DIR%ChatServer\target\ChatServer-ClassicEmu-Brasil.jar" "%DEST_DIR%\ChatServer\libs\" >nul
)

mkdir "%DEST_DIR%\GameServer\log" 2>nul
mkdir "%DEST_DIR%\LoginServer\log" 2>nul
mkdir "%DEST_DIR%\ChatServer\log" 2>nul

echo.
echo ===============================================================================
echo [SUCESSO] Publicacao concluida! Os servidores estao prontos em:
echo           %DEST_DIR%
echo.
echo           Para iniciar todos os servicos com painel visual unico, execute:
echo           2 - Emulador [Produto Final]\Aion Classic - EMU.exe
echo ===============================================================================
echo.
if "%1"=="" pause
