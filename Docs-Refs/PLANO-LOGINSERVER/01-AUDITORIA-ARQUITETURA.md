# 01 - AUDITORIA DA ARQUITETURA

## OBJETIVO
Realizar o levantamento detalhado de toda a arquitetura atual do emulador Rust (**EmuRust**), mapear os componentes legados, analisar a fragmentação entre `auth-server` e `sts-server`, avaliar o acoplamento do `game-server`, identificar a ausência do `chat-server` e desenhar a transição para a arquitetura unificada de 3 servidores isolados gerenciados pelo `Auto-Start EmuRust.exe`.

## PROBLEMA
Atualmente, o emulador Rust encontra-se fragmentado em múltiplos processos desorganizados:
1. `auth-server.exe` (escutando nas portas 2106 e 13001).
2. `sts-server.exe` (escutando na porta 6600).
3. `game-server.exe` (escutando na porta 7777).
4. Ausência de um `chat-server.exe` dedicado e isolado.
5. Inexistência de um painel de controle executável unificado (`Auto-Start EmuRust.exe`), dependendo de scripts `.bat` dispersos.
6. Falta de monitoramento em tempo real de métricas (CPU/Memória) e visualizador central de logs coloridos por servidor.

## CAUSA
O desenvolvimento inicial foi realizado como protótipos de conceito (POCs) isolados para investigar o protocolo STS e o protocolo HQ separadamente, resultando em servidores fragmentados que não refletem a arquitetura modular limpa do Java Emulator (onde LoginServer centraliza toda autenticação e STS, GameServer lida com o mundo e ChatServer processa comunicação).

## ANÁLISE
A auditoria comparativa entre o Java Retail 4.8 e o Rust atual revela:
* **Java**: Possui 3 servidores (`login-server`, `game-server`, `chat-server`). O `login-server` é responsável por todo o fluxo de entrada, criação de contas, validação de tokens e entrega das chaves de sessão para o `game-server`. O `chat-server` é um serviço separado que autentica clientes após a validação no `game-server`.
* **Rust Atual**: Separou artificialmente `auth-server` e `sts-server`. Isso gera complexidade desnecessária de deploy, concorrência no banco de dados SQLite (`aion.db`) e ausência do serviço de chat.

## SOLUÇÃO
1. Consolidar `auth-server` e `sts-server` em um único crate de alta coesão: `login-server`.
2. Manter o `game-server` como serviço isolado e otimizado.
3. Criar o novo serviço isolado `chat-server`.
4. Desenvolver o `Auto-Start EmuRust.exe` como um gerenciador de processos com GUI moderna estilo macOS/iOS/Grafana, com crash detection, auto-restart e log center unificado com identificação por cores.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/Cargo.toml`
* `Emulador-Rust/login-server/` (novo crate consolidado)
* `Emulador-Rust/game-server/`
* `Emulador-Rust/chat-server/` (novo crate)
* `Emulador-Rust/auto-start/` (novo crate para a GUI)
* `Emulador-Rust/config/launcher.json`
* `deploy/`

## IMPLEMENTAÇÃO
* Mapeamento de todos os módulos de rede, banco de dados e utilitários existentes.
* Reestruturação do workspace Cargo raiz para incluir `login-server`, `game-server`, `chat-server` e `auto-start`.
* Definição dos protocolos de comunicação inter-servidores (IPCs).

## TESTES
* Verificação da integridade das dependências no `Cargo.toml`.
* Validação do isolamento de compilação de cada crate.

## VALIDAÇÃO
* Workspace Cargo configurado e sem conflitos de compilação.
* Estrutura de diretórios criada e padronizada.

## RISCOS
* Conflito de portas e concorrência no arquivo de banco de dados SQLite `aion.db`.
* Mitigação: Uso de WAL mode no SQLite e atribuição estrita de portas no `launcher.json`.

## DEPENDÊNCIAS
* `tokio`, `rusqlite`, `serde`, `serde_json`, `krypt`, `sysinfo`.

## TO-DO
- [x] Levantar todos os arquivos e crates existentes.
- [x] Mapear dependências entre auth, sts e game servers.
- [x] Desenhar a topologia final dos 3 servidores + Launcher GUI.
- [x] Documentar o plano de migração.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
