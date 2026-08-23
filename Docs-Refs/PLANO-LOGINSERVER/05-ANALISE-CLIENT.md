# 05 - ANÁLISE DO CLIENT (AION.BIN & GAME.DLL)

## OBJETIVO
Documentar as descobertas da engenharia reversa no binário do cliente 64-bit do Aion Classic EU localizado em `Cliente\GFAion\aionclassic\bin64\Aion.bin` e `game.dll`, identificando as particularidades de inicialização, flags de linha de comando e requisitos de protocolo.

## PROBLEMA
O client Aion Classic 64-bit da Gameforge possui proteções internas, verificações estritas de versão e novos formatos de pacotes que diferem do Retail de 2015 e do emulador Java antigo. Tentar usar pacotes legados sem atender aos requisitos do `game.dll` causa congelamentos ou desconexão com mensagens genéricas como `Everything is OK. (0)` ou `Error (33)(901)`.

## CAUSA
O client x64 implementa:
1. Verificação da flag `-loginex` para ativar o Named Pipe `\\.\pipe\GameforgeClientJSONRPC`.
2. Verificação do byte `0xFD` no offset `0xA8` do pacote `SM_INIT` para desbloquear o handshake RSA/Blowfish.
3. Assinatura obrigatória `0xFF 0xFE` nos offsets `0x20..0x21` do pacote `SM_LOGIN_OK`.
4. Rejeição explícita de endereços de loopback (`127.0.0.1`) na lista de servidores (`SM_SERVER_LIST`), exigindo IP de rede local (LAN).
5. Estrutura de entradas de servidor com **21 bytes** (em vez de 20 bytes legados) para o modo NCSoft e **63 bytes** com IP ASCII para o modo Gameforge HQ.

## ANÁLISE
Do relatório de engenharia reversa (`docs/reverse/game-dll-x64-findings.md` e `docs/protocol/auth-server.md`):
* **Rotina `0x15A0E0` (Login Button)**: Exige que a sessão de login externa esteja validada ou liberada via Named Pipe.
* **Rotina `0x842301` (SM_INIT Parser)**: Lê `[rdx+0xA8]` e compara com `0xFD`. Se não for `0xFD`, descarta a chave pública RSA.
* **Rotina `0x717BE2` & `0x717B40` (SM_LOGIN_OK Validation)**: Exige flags de conta `0x3F`, flag TOS `1` no offset `0x30` e bytes mágicos `0xFF 0xFE`.
* **Rotina `0x84284D` (SM_SERVER_LIST Parser)**: Processa cada entrada com 21 bytes, validando o `CountryCode/Bracket` contra `-cc:2` e o bit 10 (`0x400`) do campo `ServerBits` para reconhecer o servidor como Classic.
* **Rotina `0x843077` (Character Counts)**: Lê `short(totalServers)` e 1 byte por servidor para contagem de personagens.

## SOLUÇÃO
Configurar o `login-server` e os scripts de inicialização do client para atender estritamente a essas 5 restrições descobertas na engenharia reversa do executável.

## ARQUIVOS ENVOLVIDOS
* `Cliente/GFAion/aionclassic/bin64/Aion.bin`
* `Cliente/GFAion/aionclassic/bin64/game.dll`
* `Cliente/GFAion/aionclassic/Start_Client_Classic_EU.bat`
* `docs/reverse/game-dll-x64-findings.md`
* `docs/protocol/auth-server.md`

## IMPLEMENTAÇÃO
* Ajuste da linha de comando do cliente com `-usehqserver -hqip:127.0.0.1 -hqport:13001 -np:127.0.0.1 -dwsm -loginex -pwd16 -npsa -probability -nospamcheck -noweb -nowebshop -st -dpetition -hidepromo -nosatab -nosarefund -dingameshop -disabletempbanner -disabledevaschedule -recserveridx:1 -old_charInstance`.
* Configuração do IP do game server como IP de LAN (`192.168.3.184`).

## TESTES
* Teste de inicialização do client via `Start_Client_Classic_EU.bat`.
* Inspeção dos logs em `AIONLOG/log.txt` para validar ausência de erros de carregamento de DLLs.

## VALIDAÇÃO
* Cliente inicializa sem erros críticos e conecta aos servidores locais.

## RISCOS
* Incompatibilidade caso o client seja atualizado no futuro.
* Mitigação: Isolamento dos parsers em módulos versionados.

## DEPENDÊNCIAS
* `Aion.bin`, `game.dll`, `Start_Client_Classic_EU.bat`.

## TO-DO
- [x] Mapear endereços e instruções do `game.dll`.
- [x] Documentar os offsets de `SM_INIT`, `SM_LOGIN_OK` e `SM_SERVER_LIST`.
- [x] Validar a necessidade do flag `-loginex`.
- [x] Validar a regra de rejeição de IP `127.0.0.1` na lista de servidores.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
