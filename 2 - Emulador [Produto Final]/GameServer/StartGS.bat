TITLE Aion Classic 5.0 - Game Server Console
color 0A
if exist "%JAVA_HOME%\bin\java.exe" set "PATH=%JAVA_HOME%\bin;%PATH%"
if exist "C:\Program Files\Java\jdk1.8.0_431\bin\java.exe" set "PATH=C:\Program Files\Java\jdk1.8.0_431\bin;%PATH%"
:START
CLS

echo.

echo Starting Aion Lightning Version 2.4 Game Server.

echo.

REM -------------------------------------  
REM Default parameters for a basic server.
java -Xms1280m -Xmx3192m -XX:MaxHeapSize=3192m -Xdebug -ea -cp ./libs/*;Encom-Game-1.8.jar com.aionemu.gameserver.GameServer
REM -------------------------------------
SET CLASSPATH=%OLDCLASSPATH%

if ERRORLEVEL 2 goto restart
if ERRORLEVEL 1 goto error
if ERRORLEVEL 0 goto end

REM Restart...
:restart
echo.
echo Administrator Restart ...
echo.
goto start

REM Error...
:error
echo.
echo Server terminated abnormaly ...
echo.
goto end

REM End...
:end
echo.
echo Server terminated ...
echo.
pause
