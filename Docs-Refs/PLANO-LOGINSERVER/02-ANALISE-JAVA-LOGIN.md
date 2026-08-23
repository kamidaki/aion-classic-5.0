# 02 - ANÁLISE DO LOGIN-SERVER JAVA

## OBJETIVO
Analisar profundamente a arquitetura, ciclo de vida, modelos de concorrência, gerenciamento de sessões, account controllers e segurança do `login-server` do emulador Java 4.8 Retail para extrair os princípios de design sem copiar valores legados de opcodes incompatíveis.

## PROBLEMA
No emulador Java, o login-server concentra autenticação, banco de dados de contas, verificação de IP, detecção de brute-force, controle de servidores de jogos registrados (`GameServerTable`) e distribuição de chaves de sessão seguras (`SessionKey`). O emulador Rust atual carecia dessa estrutura coesa e centralizada.

## CAUSA
O código Rust inicial implementou apenas manipuladores de sockets simples sem abstração de `AccountController`, `SessionManager`, `BannedIpManager` ou registro dinâmico de `GameServer`.

## ANÁLISE
Do Java `login-server/src/com/aionemu/loginserver`:
1. **`LoginServer.java`**: Ponto de entrada, inicializa threads, conexão com banco de dados MySQL, listeners de rede Netty/NIO para clientes Aion e para GameServers.
2. **`GameServerTable.java` & `GameServerInfo.java`**: Gerencia lista de GameServers registrados, status (Online/Offline), contagem de players e limites.
3. **`AccountController.java` & `AccountDAO.java`**: Busca contas, suporta `auto-create-accounts`, valida hash de senha, armazena último IP, status de ativação e nível de acesso (GM/Player).
4. **`SessionManager.java`**: Mapeia `accountId` para `SessionKey` gerada criptograficamente. Quando o client escolhe o servidor, a `SessionKey` é transmitida tanto para o client quanto para o `GameServer` via conexão interna para validação de entrada no mundo.
5. **`BannedIpController.java` & `FloodProtection.java`**: Previne ataques de negação de serviço e força bruta limitando conexões por minuto por IP.

## SOLUÇÃO
Modelar o novo crate `login-server` em Rust com as mesmas camadas conceituais:
* `AccountManager`: Gerenciamento e auto-criação de contas com transações seguras no SQLite (`aion.db`).
* `SessionRegistry`: Registro de sessões ativas com expiração automática.
* `GameServerRegistry`: Tabela de servidores de jogos conectados e status.
* `SecurityController`: Rate limiter por IP e bloqueio temporário após falhas de autenticação.
* `AionNetListener`: Suporte aos múltiplos protocolos de entrada (porta clássica 2106, porta HQ 13001, porta STS 6600 e Named Pipe).

## ARQUIVOS ENVOLVIDOS
* `Docs-Refs/JAVA EMU - 4.8 RETAIL/login-server/`
* `Emulador-Rust/login-server/src/main.rs`
* `Emulador-Rust/login-server/src/account/mod.rs`
* `Emulador-Rust/login-server/src/session/mod.rs`
* `Emulador-Rust/login-server/src/security/mod.rs`
* `Emulador-Rust/login-server/src/gameserver/mod.rs`

## IMPLEMENTAÇÃO
* Extração dos padrões de design assíncrono e abstração de sessões do Java.
* Implementação dos módulos em Rust com `tokio` e `parking_lot`/`Arc<Mutex>`.

## TESTES
* Testes unitários para `AccountManager` (criação, busca e contagem de personagens).
* Testes unitários para `SessionRegistry` (emissão, expiração e validação de tokens).
* Testes de rate limiting e bloqueio por IP.

## VALIDAÇÃO
* Sessões geradas de forma idempotente e segura.
* Auto-criação de contas funcionando para qualquer credencial submetida.

## RISCOS
* Bloquear IPs legítimos caso a tolerância do rate limiter seja muito restrita.
* Mitigação: Parâmetros de tolerância configuráveis no `launcher.json`.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`, `rand`, `parking_lot`, `chrono`.

## TO-DO
- [x] Analisar `GameServerTable.java` e `SessionKey.java` do Java.
- [x] Analisar `AccountController.java` e lógica de auto-criação de contas.
- [x] Projetar `AccountManager` e `SessionRegistry` em Rust.
- [x] Integrar com `aion.db`.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
