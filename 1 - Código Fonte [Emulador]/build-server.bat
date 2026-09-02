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

REM --- 4. Extrair e Publicar os Servidores ---
echo [*] Publicando LoginServer...
powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%LoginServer\target\LoginServer.zip' -DestinationPath '%DEST_DIR%\LoginServer' -Force"

echo [*] Publicando GameServer...
powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%GameServer\target\GameServer.zip' -DestinationPath '%DEST_DIR%\GameServer' -Force"

echo [*] Publicando ChatServer...
powershell -NoProfile -Command "Expand-Archive -Path '%ROOT_DIR%ChatServer\target\ChatServer.zip' -DestinationPath '%DEST_DIR%\ChatServer' -Force"

mkdir "%DEST_DIR%\GameServer\log" 2>nul
mkdir "%DEST_DIR%\LoginServer\log" 2>nul
mkdir "%DEST_DIR%\ChatServer\log" 2>nul

REM --- 5. Criar Inicializador Unificado StartAll.bat ---
echo [*] Criando scripts de inicializacao unificados...

(
echo @echo off
echo title Aion Classic 5.0 - Servidores
echo echo ===============================================================================
echo echo               INICIANDO AION CLASSIC 5.0 EU EMULATOR SUITE
echo echo ===============================================================================
echo.
echo echo [*] Iniciando LoginServer...
echo cd /d "%%~dp0LoginServer"
echo start "Aion 5.0 - LoginServer" cmd /k "StartLS.bat"
echo timeout /t 2 /nobreak ^>nul
echo.
echo echo [*] Iniciando ChatServer...
echo cd /d "%%~dp0ChatServer"
echo start "Aion 5.0 - ChatServer" cmd /k "StartCS.bat"
echo timeout /t 2 /nobreak ^>nul
echo.
echo echo [*] Iniciando GameServer...
echo cd /d "%%~dp0GameServer"
echo start "Aion 5.0 - GameServer" cmd /k "StartGS.bat"
echo.
echo echo [OK] Todos os servidores foram iniciados em janelas separadas!
) > "%DEST_DIR%\StartAll.bat"

(
echo @echo off
echo title Aion Classic 5.0 - Parar Servidores
echo echo Encerrando processos Java do Aion Classic...
echo taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - LoginServer*" /T ^>nul 2^>^&1
echo taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - GameServer*" /T ^>nul 2^>^&1
echo taskkill /F /FI "WINDOWTITLE eq Aion 5.0 - ChatServer*" /T ^>nul 2^>^&1
echo echo Servidores finalizados com sucesso!
) > "%DEST_DIR%\StopAll.bat"

echo.
echo ===============================================================================
echo [SUCESSO] Publicacao concluida! Os servidores estao prontos em:
echo           %DEST_DIR%
echo.
echo           Para iniciar tudo de uma vez, execute:
echo           2 - Emulador [Produto Final]\StartAll.bat
echo ===============================================================================
echo.
if "%1"=="" pause
