# 12 - IMPLEMENTAÇÃO DO CHAT-SERVER EM RUST

## OBJETIVO
Implementar do zero o crate `chat-server` em Rust como um microserviço isolado e de alta performance, responsável por gerenciar canais de chat, whispers, broadcast de mensagens e comunicação inter-servidor com o Game-Server.

## PROBLEMA
A ausência de um ChatServer dedicado forçava a sobrecarga do GameServer ou deixava canais globais (LFG, Comércio, Região) inoperantes no client.

## CAUSA
O emulador Rust inicial não contemplava o subsistema de chat isolado presente no Java.

## ANÁLISE
O `chat-server` necessita de:
1. **Network Listener (Porta 10241)**:
   * `CM_CHAT_INI` (0x01): Handshake inicial com o client. Responde com `SM_CHAT_INI`.
   * `CM_PLAYER_AUTH` (0x02): Validação do jogador com `playerId` e `chatToken`. Responde com `SM_PLAYER_AUTH_RESPONSE`.
   * `CM_CHANNEL_JOIN` (0x03): Inscrição em canal (Região/LFG/Legião). Responde com `SM_CHANNEL_RESPONSE`.
   * `CM_CHANNEL_MESSAGE` (0x05): Recebe mensagem do jogador e faz broadcast para todos os inscritos via `SM_CHANNEL_MESSAGE`.
   * `CM_PING` (0x06): Resposta a keepalive.
2. **Channel Manager**:
   * Gerenciamento de canais por ID, nome e mapa.
   * Lista thread-safe de inscritos usando `parking_lot::RwLock` e `tokio::sync::mpsc`.
   * Rate limiting de mensagens por jogador (anti-spam).
3. **IPC com Game-Server**:
   * Porta de controle ou shared state para registrar quando um jogador ganha permissão de chat no mundo.

## SOLUÇÃO
Criar o crate `Emulador-Rust/chat-server/`:
* `Cargo.toml`: Dependências Tokio, Bytes, Serde.
* `src/main.rs`: Inicialização do serviço, leitura da seção `[chat-server]` do `launcher.json` e loop assíncrono.
* `src/channels.rs`: Estrutura de canais de chat com suporte a broadcast lock-free.
* `src/protocol.rs`: Serialização e desserialização dos pacotes de chat do Aion.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/chat-server/Cargo.toml`
* `Emulador-Rust/chat-server/src/main.rs`
* `Emulador-Rust/chat-server/src/channels.rs`
* `Emulador-Rust/chat-server/src/protocol.rs`
* `Emulador-Rust/chat-server/src/config.rs`

## IMPLEMENTAÇÃO
* Criação do crate `chat-server`.
* Implementação dos handlers de pacotes de chat.
* Implementação do `ChannelManager` thread-safe.

## TESTES
* Teste unitário de criação e envio de mensagens em canais.
* Teste de concorrência com 1.000 clientes simulados enviando mensagens simultâneas.
* Teste de detecção e mute por flood.

## VALIDAÇÃO
* O `chat-server.exe` inicia na porta `10241` e responde a handshakes de chat.
* Opera como processo independente, com logs isolados em `logs/chat-server/`.

## RISCOS
* Deadlock em canais de broadcast sob altíssima concorrência.
* Mitigação: Uso de canais não-bloqueantes (`tokio::sync::broadcast`) com buffer circular.

## DEPENDÊNCIAS
* `tokio`, `bytes`, `serde`, `serde_json`, `parking_lot`.

## TO-DO
- [x] Criar manifest `chat-server/Cargo.toml`.
- [x] Implementar `ChannelManager` e broadcast de mensagens.
- [x] Implementar protocolo de rede de chat do Aion.
- [x] Configurar logging isolado e leitura de `launcher.json`.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
