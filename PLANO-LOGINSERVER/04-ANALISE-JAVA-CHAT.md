# 04 - ANÁLISE DO CHAT-SERVER JAVA

## OBJETIVO
Analisar a arquitetura, protocolos de rede, pacotes de client e comunicação com o GameServer do `chat-server` no emulador Java 4.8 Retail, a fim de subsidiar a criação do novo crate `chat-server` isolado no Rust.

## PROBLEMA
No emulador Rust atual, não existia um `chat-server` isolado. Mensagens e canais eram manipulados de forma rudimentar dentro do game-server ou não estavam completamente disponíveis, impedindo canais globais, whispers seguros e separação de carga.

## CAUSA
O foco inicial do projeto foi emulação de movimento e spawning de NPCs, postergando a implementação de um subsistema de chat dedicado.

## ANÁLISE
Do Java `chat-server/src/com/aionemu/chatserver`:
1. **`ChatServer.java`**: Inicializa o servidor de chat em porta dedicada (porta cliente Netty na `10241` e porta de sincronização com GameServer).
2. **`network/aion/clientpackets/`**:
   * `CM_CHAT_INI` (Opcode 0x01): Handshake inicial do client de chat.
   * `CM_PLAYER_AUTH` (Opcode 0x02): Autenticação do jogador usando `token` e `playerId` fornecidos pelo GameServer.
   * `CM_CHANNEL_JOIN` (Opcode 0x03): Entrada em canal de chat (Região, Mapa, LFG, Comércio).
   * `CM_CHANNEL_LEAVE` (Opcode 0x04): Saída de canal.
   * `CM_CHANNEL_MESSAGE` (Opcode 0x05): Envio de mensagem para um canal específico.
   * `CM_PING` (Opcode 0x06): Keepalive de conexão.
3. **`network/aion/serverpackets/`**:
   * `SM_CHAT_INI` (Opcode 0x01): Resposta ao handshake de inicialização de chat.
   * `SM_PLAYER_AUTH_RESPONSE` (Opcode 0x02): Confirmação de autenticação do jogador.
   * `SM_CHANNEL_RESPONSE` (Opcode 0x03): Status de entrada em canais.
   * `SM_CHANNEL_MESSAGE` (Opcode 0x04): Broadcast de mensagem para todos os inscritos no canal.
4. **`network/gameserver/`**:
   * O GameServer conecta no ChatServer logo após subir, enviando `GsAuthRequest` e registrando os canais disponíveis por mapa. Quando um player loga no mundo, o GameServer notifica o ChatServer para autorizar o jogador.

## SOLUÇÃO
Criar o novo crate `chat-server` em Rust (`Emulador-Rust/chat-server/`):
* Listener TCP assíncrono para o client Aion na porta configurável (padrão `10241`).
* Listener IPC assíncrono para conexão do `game-server`.
* Gerenciador de canais em memória (`ChannelManager`) com suporte a broadcast lock-free e controle de flood/spam.
* Módulos de serialização e desserialização binária dos pacotes `CM_*` e `SM_*`.

## ARQUIVOS ENVOLVIDOS
* `JAVA EMU - 4.8 RETAIL/chat-server/`
* `Emulador-Rust/chat-server/Cargo.toml`
* `Emulador-Rust/chat-server/src/main.rs`
* `Emulador-Rust/chat-server/src/channels/mod.rs`
* `Emulador-Rust/chat-server/src/net/aion/mod.rs`
* `Emulador-Rust/chat-server/src/net/gameserver/mod.rs`

## IMPLEMENTAÇÃO
* Criação do crate `chat-server` no workspace Cargo.
* Implementação dos handlers de pacotes de chat com `bytes` e `tokio::net::TcpListener`.
* Implementação do gerenciador de canais com canais `tokio::sync::broadcast`.

## TESTES
* Teste unitário de criação e destruição de canais.
* Teste de broadcast de mensagens entre múltiplos clientes conectados.
* Teste de rate limiting de mensagens para prevenção de spam.

## VALIDAÇÃO
* Cliente de teste envia `CM_CHAT_INI` e recebe `SM_CHAT_INI`.
* Autenticação e entrada em canal validadas com sucesso.

## RISCOS
* Vazamento de memória por acúmulo de inscritos em canais fechados.
* Mitigação: Remoção automática de inscritos ao detectar desconexão de socket.

## DEPENDÊNCIAS
* `tokio`, `serde`, `parking_lot`, `bytes`, `tracing`.

## TO-DO
- [x] Mapear opcodes de chat do Java (`CM_CHAT_INI`, `CM_PLAYER_AUTH`, etc.).
- [x] Desenhar a arquitetura do crate `chat-server`.
- [x] Implementar o `ChannelManager` e handlers de pacotes.
- [x] Integrar com o `game-server`.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
