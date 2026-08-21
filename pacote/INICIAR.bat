@echo off
REM Duplo clique aqui. O -ExecutionPolicy Bypass existe porque o Windows bloqueia
REM script PowerShell baixado da internet por padrao, e o erro nao explica isso.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar.ps1"
