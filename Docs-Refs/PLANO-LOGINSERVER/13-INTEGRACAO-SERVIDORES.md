# 13 - INTEGRAÇÃO ENTRE OS 3 SERVIDORES

## OBJETIVO
Definir e validar os protocolos de comunicação inter-processos (IPC), handshakes e ciclo de vida entre o `login-server`, `game-server` e `chat-server`.

## PROBLEMA
Os três servidores precisam operar de forma coesa sem acoplamento direto de código, garantindo que o jogador passe de forma transparente pelo Login, entre no Mundo (Game) e converse nos Canais (Chat).

## CAUSA
A necessidade de arquitetura modular distribuída sem dependências circulares.

## ANÁLISE
O fluxo de integração opera em 3 camadas:
1. **Login -> Game Server**:
   * O cliente autentica no `login-server` (via porta 13001/2106 ou STS 6600).
   * O `login-server` grava o token/chave na tabela `sessions` (`token`, `account_name`, `expires_at`).
   * O cliente recebe o `SESSION_KEY` e conecta no `game-server` (porta 7777).
   * O `game-server` valida a `SESSION_KEY` consultando `sessions` e associa o jogador à sua conta.
2. **Game Server -> Chat Server**:
   * Quando o `game-server` inicializa o jogador no mundo, emite um token de chat efêmero.
   * O cliente conecta no `chat-server` (porta 10241) enviando o token.
   * O `chat-server` valida o token e inscreve o jogador nos canais apropriados (ex: canal da região onde o jogador está no mapa).
3. **Resiliência a Falhas**:
   * Se o `login-server` reiniciar, jogadores já conectados no `game-server` e `chat-server` continuam jogando normalmente.
   * Se o `chat-server` reiniciar, o cliente reconecta automaticamente sem derrubar o jogo.
   * Se o `game-server` reiniciar, o `login-server` atualiza o status para Offline e bloqueia novas entradas até que o mundo volte a estar ativo.

## SOLUÇÃO
Padronizar a comunicação inter-servidores usando o banco de dados `aion.db` (em modo WAL de alta velocidade) para estados persistentes/sessões e sockets TCP leves para notificações em tempo real.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/login-server/src/main.rs`
* `Emulador-Rust/game-server/src/main.rs`
* `Emulador-Rust/chat-server/src/main.rs`
* `Emulador-Rust/aion.db`

## IMPLEMENTAÇÃO
* Implementação do handshake e validação de tokens nas três pontas.
* Tratamento de desconexões e reconexões idempotentes.

## TESTES
* Teste de fluxo completo: Login -> Game -> Chat.
* Teste de resiliência: Derrubar o `chat-server` durante o jogo e validar que o `game-server` continua rodando.
* Teste de resiliência: Derrubar o `login-server` durante o jogo e validar que o jogador continua conectado.

## VALIDAÇÃO
* Fluxo end-to-end executado com sucesso e logs de confirmação nos 3 servidores.

## RISCOS
* Sessões fantasmas ou expiradas acumuladas no banco de dados.
* Mitigação: Tarefa periódica de limpeza (`cleanup_expired_sessions`) a cada 5 minutos no Login-Server.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`.

## TO-DO
- [x] Mapear o ciclo de vida e handshakes entre os 3 servidores.
- [x] Implementar a validação de sessões compartilhada.
- [x] Testar o isolamento e tolerância a falhas.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
