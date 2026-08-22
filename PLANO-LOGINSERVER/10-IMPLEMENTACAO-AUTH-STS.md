# 10 - INTEGRAÇÃO DE AUTH E STS NO LOGIN-SERVER

## OBJETIVO
Integrar o serviço STS (porta `6600`) e o provedor de Named Pipe Windows (`\\.\pipe\GameforgeClientJSONRPC`) nativamente dentro do binário `login-server.exe`, eliminando a necessidade do processo separado `sts-server.exe` ou `launcher.exe`.

## PROBLEMA
Executar `sts-server.exe` e `auth-server.exe` como dois processos separados aumentava a sobrecarga operacional, exigia múltiplos logs e duplicava o acesso concorrente ao arquivo de banco de dados `aion.db`.

## CAUSA
Separação histórica no repositório de desenvolvimento onde o STS foi prototipado como uma aplicação independente.

## ANÁLISE
O protocolo STS do Aion utiliza HTTP 1.0 simples sobre TCP:
* Framing delimitado por `\r\n\r\n` com cabeçalhos `l:<content_length>` e `s:<sequence_number>`.
* Endpoints essenciais:
  1. `POST /Sts/Connect`: Handshake inicial do cliente com `ConnType`, `Build` e `ProcessId`.
  2. `POST /Auth/LoginStart`: Validação da conta e retorno do XML `<Reply>` contendo `UserId`, `LoginName`, `UserName`, `GameAccountId`, `Session` e `LocationId`.
  3. `POST /Auth/RequestGameToken`: Geração do token temporário de sessão para o GameServer.
  4. `POST /Sts/Ping`: Keepalive contínuo enviado a cada 20 segundos.
  5. `POST /Account/GetUserInfo`: Metadados da conta federada.
  6. `POST /Auth/LogoutMyClient`: Finalização limpa de sessão.

Além disso, o Named Pipe `\\.\pipe\GameforgeClientJSONRPC` precisa responder aos métodos JSON-RPC:
* `ClientLibrary.isClientRunning` -> `true`
* `ClientLibrary.initSession` -> `session_id`
* `ClientLibrary.queryGameDisplayLocale` -> `en_GB`
* `ClientLibrary.queryAuthorizationCode` -> `AUTHN_TOKEN` em base64
* `ClientLibrary.queryGameAccountName` -> `username`
* `ClientLibrary.queryGameAccountNumericId` -> `numeric_id`

## SOLUÇÃO
Embutir o listener STS assíncrono na porta `6600` e a thread do Named Pipe diretamente dentro do `login-server`, compartilhando a mesma instância de banco de dados (`Arc<AuthDb>`).

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/login-server/src/net/sts/mod.rs`
* `Emulador-Rust/login-server/src/net/sts/protocol.rs`
* `Emulador-Rust/login-server/src/net/sts/api.rs`
* `Emulador-Rust/login-server/src/net/pipe/mod.rs`
* `Emulador-Rust/login-server/src/net/pipe/wyn.rs`

## IMPLEMENTAÇÃO
* Portabilidade dos handlers do STS para dentro de `login-server/src/net/sts/`.
* Suporte a nomes de usuário dinâmicos no `login_reply` e `GetUserInfo`.
* Registro das sessões geradas diretamente na tabela `sessions` do `aion.db`.

## TESTES
* Teste de integração do Named Pipe JSON-RPC.
* Teste de handshake STS (`Connect` -> `LoginStart` -> `RequestGameToken` -> `Ping`).
* Verificação da integridade das chaves na tabela `sessions`.

## VALIDAÇÃO
* O `login-server` atende simultaneamente conexões no Named Pipe, na porta STS 6600 e nas portas de login 13001 e 2106.

## RISCOS
* Bloqueio do loop de eventos caso a leitura do Named Pipe trave.
* Mitigação: O Named Pipe roda em thread dedicada desacoplada do runtime Tokio.

## DEPENDÊNCIAS
* `tokio`, `quick-xml`, `base64`, `krypt`.

## TO-DO
- [x] Migrar módulo STS para o crate `login-server`.
- [x] Migrar módulo Named Pipe para o crate `login-server`.
- [x] Ajustar retorno de username dinâmico.
- [x] Testar integração ponta a ponta.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
