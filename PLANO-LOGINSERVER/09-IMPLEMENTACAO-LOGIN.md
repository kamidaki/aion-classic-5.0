# 09 - IMPLEMENTAÇÃO DO LOGIN-SERVER UNIFICADO

## OBJETIVO
Implementar o novo crate `login-server` consolidando os listeners NCSoft (`2106`), Gameforge HQ (`13001`), gerenciador de contas com `auto-create` e registro atômico de sessões em SQLite (`aion.db`).

## PROBLEMA
Antes, o `auth-server` lidava apenas com o protocolo HQ de forma estática e não integrava o STS ou a auto-criação dinâmica de contas a partir do payload recebido.

## CAUSA
O código antigo hardcodava o usuário `teste` e não extraía o nome do usuário a partir dos pacotes de credenciais.

## ANÁLISE
O `login-server` deve suportar simultaneamente:
1. Conexões na porta `2106` para clientes modo clássico.
2. Conexões na porta `13001` para clientes modo Gameforge HQ.
3. Extração dinâmica do nome da conta em texto plano (offset 3) ou descriptografado.
4. Consulta ou criação automática no banco de dados SQLite (`aion.db`).
5. Retorno de `SM_LOGIN_OK` e `SM_SERVER_LIST` com o IP de anúncio configurado (`192.168.3.184`).
6. Emissão de `SESSION_KEY` com campos de erro zerados (`bytes[14..18] == [0, 0, 0, 0]`).

## SOLUÇÃO
Criar o módulo `login-server` com:
* `src/main.rs`: Inicialização dos listeners e carregamento do `launcher.json`.
* `src/db.rs`: Camada SQLite com pool e prepared statements para criação e contagem de personagens por conta.
* `src/net/hq.rs`: Handler da porta `13001`.
* `src/net/ncsoft.rs`: Handler da porta `2106`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/login-server/src/main.rs`
* `Emulador-Rust/login-server/src/db.rs`
* `Emulador-Rust/login-server/src/net/mod.rs`
* `Emulador-Rust/login-server/src/net/hq.rs`
* `Emulador-Rust/login-server/src/net/ncsoft.rs`

## IMPLEMENTAÇÃO
* Implementação do parser dinâmico de credenciais.
* Integração com a tabela `accounts` e `sessions` do `aion.db`.
* Implementação de serialização segura de `SERVER_LIST`.

## TESTES
* Teste unitário de login com novas contas (auto-criação).
* Teste de emissão de session key.
* Teste de seleção de servidor.

## VALIDAÇÃO
* Servidor escuta em `0.0.0.0:13001` e `0.0.0.0:2106`.
* Responde corretamente com `AUTH_GREETING`, `LOGIN_OK`, `SERVER_LIST` e `SESSION_KEY`.

## RISCOS
* Concorrência de escrita simultânea no SQLite.
* Mitigação: Uso de `rusqlite` com `journal_mode = WAL` e `busy_timeout = 5000`.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`, `serde`, `serde_json`, `krypt`.

## TO-DO
- [x] Criar estrutura de pastas do `login-server`.
- [x] Implementar handlers de rede HQ e NCSoft.
- [x] Implementar camada de banco de dados com auto-create.
- [x] Testar e validar.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
