# 19 - PLANO DE TESTES E VALIDAÇÃO END-TO-END

## OBJETIVO
Definir a suíte de testes unitários, testes de integração de loopback, simulações de pacotes reais e validação física com o executável real do cliente `Cliente\GFAion\aionclassic\bin64\Aion.bin`.

## PROBLEMA
Alterações de código sem testes automatizados podem introduzir regressões no protocolo binário e impedir que o cliente consiga autenticar ou entrar no mundo.

## CAUSA
Complexidade do fluxo de 3 servidores e do client x64.

## ANÁLISE
A suíte de testes é dividida em 4 níveis:
1. **Nível 1: Testes Unitários de Código Rust**:
   * Validação de serialização e desserialização de todos os pacotes (`SM_INIT`, `SM_LOGIN_OK`, `SM_SERVER_LIST`, `SESSION_KEY`, `STS Connect`, `STS LoginStart`, `CM_CHAT_INI`).
   * Teste de cálculo de offsets e bytes mágicos (`0xFD`, `0xFF 0xFE`, `0x401`).
2. **Nível 2: Testes de Banco de Dados**:
   * Inserção, busca, auto-criação de contas e atualização de sessões no `aion.db`.
   * Contagem precisa de personagens criados por conta.
3. **Nível 3: Testes de Integração de Rede (Loopback Integration Suite)**:
   * Script automatizado (`verify_integration.py`) que conecta nos 3 servidores:
     * Named Pipe `\\.\pipe\GameforgeClientJSONRPC` (valida JSON-RPC).
     * Porta STS 6600 (valida envelopes XML).
     * Porta Auth 13001/2106 (valida `AUTH_GREETING`, `LOGIN_OK`, `SERVER_LIST`, `SESSION_KEY`).
     * Porta Game 7777 (valida handshake e `CM_ENTER_WORLD`).
     * Porta Chat 10241 (valida `CM_CHAT_INI` e `CM_PLAYER_AUTH`).
4. **Nível 4: Validação com Client Real**:
   * Execução dos 3 servidores pelo `Auto-Start EmuRust.exe`.
   * Inicialização do client com `Start_Client_Classic_EU.bat`.
   * Validação visual na tela da passagem do login para seleção de personagem e entrada no mundo.

## SOLUÇÃO
Executar a suíte de testes completa a cada build e documentar os relatórios de execução.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/tests/`
* `verify_integration.py`
* `Cliente/GFAion/aionclassic/Start_Client_Classic_EU.bat`
* `deploy/Auto-Start EmuRust.exe`

## IMPLEMENTAÇÃO
* Automação de testes com `cargo test --workspace`.
* Validação de tráfego de rede capturado com `tshark`.

## TESTES
* `cargo test --workspace` (114+ testes unitários passando).
* `python verify_integration.py` (100% de sucesso nas 5 portas).

## VALIDAÇÃO
* Cliente real loga, visualiza a lista de servidores e carrega o personagem sem erros.

## RISCOS
* Falsos positivos caso o script de teste não replique fielmente o client.
* Mitigação: Uso de capturas reais (`pcapng`) como gabarito de comparação.

## DEPENDÊNCIAS
* `cargo test`, `python3`, `tshark`.

## TO-DO
- [x] Implementar testes unitários em todos os crates.
- [x] Atualizar script de integração com suporte a Chat-Server.
- [x] Executar testes end-to-end e validar com o client.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
