@echo off

set "ENABLE_DXVK=1"

set "ACC="
if not "%~1"=="" set "ACC=-account:%~1"
set "PASS="
if not "%~2"=="" set "PASS=-password:%~2"

start bin64\Aion.bin -ip:127.0.0.1 -port:2106 %ACC% %PASS% -lang:ENG -cc:2 -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu