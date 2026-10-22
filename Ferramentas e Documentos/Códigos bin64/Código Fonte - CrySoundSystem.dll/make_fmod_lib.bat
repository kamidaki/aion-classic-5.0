@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "d:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Códigos bin64\Código Fonte - CrySoundSystem.dll"
lib.exe /def:fmodex64.def /machine:x64 /out:fmodex64.lib
echo Lib result: %errorlevel%
