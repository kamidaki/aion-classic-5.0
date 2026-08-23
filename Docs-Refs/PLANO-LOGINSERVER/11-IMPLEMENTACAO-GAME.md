# 11 - IMPLEMENTAÇÃO E ISOLAMENTO DO GAME-SERVER

## OBJETIVO
Garantir o isolamento total do `game-server` como processo independente, mantendo sua engine de alta performance (20 TPS), carregamento de static data e comunicação segura com o Login-Server e Chat-Server.

## PROBLEMA
O GameServer precisava ler suas configurações do `launcher.json` centralizado, gravar seus próprios logs isolados e validar sessões recebidas de forma independente, sem depender de scripts ou de outros executáveis para sua lógica de mundo.

## CAUSA
Adaptação da estrutura antiga para o novo modelo de 3 servidores isolados com gerenciamento unificado.

## ANÁLISE
O `game-server` em Rust possui:
1. **World Engine**: Grid 3D de entidades com suporte a 20 TPS.
2. **Static Data Loader**:
   * `39.747` NPCs de `data/client/npcs/client_npcs.xml`
   * `76.693` Itens de `data/client/items/client_items.xml`
   * `11.476` Skills de `data/client/skills/`
   * `1.254` Spawns de `data/spawns.csv`
   * Kits iniciais para 8 classes de `data/itens_iniciais.csv`
3. **Network Listener (Porta 7777)**:
   * Handshake de criptografia dinâmico com chave estática/sessão.
   * Recepção de `CM_ENTER_WORLD` e validação da `SessionKey`.
   * Envio de `SM_CHARACTER_LIST` e entrada no mundo.

## SOLUÇÃO
* Atualizar o `game-server` para carregar suas configurações da seção `[game-server]` do `launcher.json`.
* Adicionar suporte ao cliente IPC que notifica o `chat-server` quando um jogador entra no mundo (`PlayerEnterWorldEvent`).
* Garantir que todas as saídas de log sigam o padrão unificado e sejam gravadas em `logs/game-server/YYYY-MM-DD.log`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/game-server/Cargo.toml`
* `Emulador-Rust/game-server/src/main.rs`
* `Emulador-Rust/game-server/src/game/mod.rs`
* `Emulador-Rust/game-server/src/net/mod.rs`
* `Emulador-Rust/game-server/src/ipc/mod.rs`

## IMPLEMENTAÇÃO
* Implementação do parser de `launcher.json` para o `game-server`.
* Adição do módulo IPC para comunicação com `chat-server`.
* Garantia de tratamento de graceful shutdown em sinais `SIGINT`/`SIGTERM`.

## TESTES
* Teste de inicialização autônoma do `game-server`.
* Teste de carga de carregamento de NPCs e Itens em memória (< 3 segundos).
* Teste de conexão de client na porta 7777.

## VALIDAÇÃO
* `game-server` sobe e executa de forma totalmente isolada.
* Se o `login-server` ou `chat-server` for reiniciado, o `game-server` permanece estável sem cair.

## RISCOS
* Timeout na validação de sessão caso o Login-Server esteja temporariamente ocupado.
* Mitigação: Consulta direta à tabela `sessions` no SQLite compartilhado com WAL mode.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`, `quick-xml`, `crossbeam`, `krypt`.

## TO-DO
- [x] Isolar o processo do `game-server`.
- [x] Conectar com a seção `[game-server]` do `launcher.json`.
- [x] Implementar logging físico diário isolado.
- [x] Validar estabilidade de 20 TPS.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
