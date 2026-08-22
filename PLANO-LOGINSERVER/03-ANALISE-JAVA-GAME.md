# 03 - ANÁLISE DO GAME-SERVER JAVA

## OBJETIVO
Analisar a arquitetura, ciclo de vida, modelos de tick rate (loop de jogo), gerenciamento de entidades (jogadores, NPCs, monstros, itens), carregamento de dados estáticos e protocolos de comunicação do `game-server` do Java 4.8 Retail.

## PROBLEMA
O GameServer precisa gerenciar um mundo complexo com dezenas de milhares de entidades simultâneas em alta performance, além de sincronizar sessões recebidas do LoginServer e rotear tráfego social para o ChatServer sem bloquear o loop principal de jogo.

## CAUSA
Servidores em linguagens com Garbage Collection (como Java) sofrem com pausas de GC em servidores de alta densidade populacional. No Rust, o gerenciamento de memória e concorrência é sem GC, permitindo execução contínua com tick rate fixo de 20 TPS (50ms por tick).

## ANÁLISE
Do Java `game-server/src/com/aionemu/gameserver`:
1. **`GameServer.java`**: Ponto de entrada, inicialização de pool de threads, timers, carregamento de XMLs de static data (itens, npcs, skills, spawns, quests).
2. **`World.java` & `MapRegion.java`**: Gerencia posicionamento espacial das entidades, grid de visibilidade (broadphase) e broadcast de pacotes de movimento para jogadores no mesmo quadrante.
3. **`network/loginserver/LoginServer.java`**: Cliente TCP que conecta no `login-server` (porta 9014 no Java), anuncia status do GameServer, número de jogadores online e valida `SessionKey` recebida dos clientes que conectam na porta 7777 (`CM_ENTER_WORLD`).
4. **`network/chatserver/ChatServer.java`**: Cliente TCP que conecta no `chat-server` para registrar canais de mapa, autenticar permissões de whisper e sincronizar lista de amigos/legião.
5. **`model/gameobjects/`**: Hierarquia de entidades: `AionObject` -> `VisibleObject` -> `Creature` -> `Player` / `Npc` / `Monster`.

## SOLUÇÃO
No Rust `game-server`:
* Manter o loop de jogo a 20 TPS com `tokio` timers de alta precisão.
* Preservar o carregamento dos templates (39.747 NPCs, 76.693 Itens, 11.476 Skills, 1.254 Spawns) via `quick-xml` e cache em memória.
* Implementar o canal de IPC com o `login-server` para validação atômica de sessões e contagem de jogadores.
* Implementar o canal de IPC com o `chat-server` para autenticação de canais.

## ARQUIVOS ENVOLVIDOS
* `JAVA EMU - 4.8 RETAIL/game-server/`
* `Emulador-Rust/game-server/src/main.rs`
* `Emulador-Rust/game-server/src/game/`
* `Emulador-Rust/game-server/src/net/`

## IMPLEMENTAÇÃO
* Refatoração do módulo de rede do `game-server` para desacoplar handlers e aceitar sessões transferidas do novo `login-server`.
* Implementação do cliente IPC assíncrono para o `chat-server`.

## TESTES
* Teste de carga de carregamento de XMLs de dados estáticos.
* Teste do loop de 20 TPS (estabilidade de delta time).
* Teste de spawn e visibilidade de 1.254 NPCs.

## VALIDAÇÃO
* Entrada de personagens no mundo sem crashes ou descompasso de tick.
* Validação de chave de sessão e associação correta com a conta no `aion.db`.

## RISCOS
* Bloqueio do loop de jogo por operações síncronas de I/O de disco.
* Mitigação: Todas as queries de banco de dados e comunicação de rede são executadas assincronamente com `tokio::spawn_blocking` ou canais mpsc.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`, `quick-xml`, `crossbeam`, `glam`.

## TO-DO
- [x] Analisar ciclo de vida do `World` e `MapRegion` no Java.
- [x] Analisar protocolo `network/loginserver` e `network/chatserver` no Java.
- [x] Verificar carregamento de templates e spawns no Rust `game-server`.
- [x] Documentar os requisitos de integração IPC.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
