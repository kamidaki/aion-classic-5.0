@echo off
setlocal

set "ENABLE_DXVK=1"

REM ============================================================
REM  IMPORTANTE: O formulario in-game do Aion Classic EU x64
REM  com -noweb NAO envia CM_LOGIN pelo socket TCP ao clicar OK.
REM  As credenciais DEVEM ser passadas via -account: -password:.
REM
REM  Uso: Start_Client_Classic_EU.bat [conta] [senha]
REM  Exemplo: Start_Client_Classic_EU.bat minhaconta minhasenha

REM BACKUP: start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -account:terrestre -password:terrestre -lang:ENG -cc:2 -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu
REM ============================================================

start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -account:terrestre -password:terrestre -lang:ENG -cc:2 -nowebshop