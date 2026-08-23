# 08 - ARQUITETURA FINAL DO EMURUST

## OBJETIVO
Definir a topologia completa do workspace Cargo, divisão de crates, responsabilidades, ciclo de vida e concorrência dos 3 servidores isolados (`login-server`, `game-server`, `chat-server`) e do gerenciador unificado (`auto-start`).

## PROBLEMA
A estrutura antiga do repositório possuía dependências confusas e executáveis fragmentados (`auth-server`, `sts-server`, `launcher`), dificultando a manutenção e a operação.

## CAUSA
Evolução incremental desordenada sem um plano diretor centralizado.

## ANÁLISE
A arquitetura final do workspace deve conter:

```text
Emulador-Rust/
 Cargo.toml (Virtual Workspace)
 login-server/             -> Binário: login-server.exe
    Cargo.toml
    src/
        main.rs
        account/          (Modelos de contas e auto-create)
        session/          (Sessões ativas e tokens)
        security/         (Rate limiter e anti-bruteforce)
        net/
           ncsoft/       (Listener porta 2106)
           hq/           (Listener porta 13001)
           sts/          (Listener porta 6600)
           pipe/         (Named Pipe Gameforge)
        db/               (SQLite / aion.db)

 game-server/              -> Binário: game-server.exe
    Cargo.toml
    src/
        main.rs
        game/             (World, NPCs, Spawns, Skills, Items)
        net/              (Listener porta 7777)
        ipc/              (Clientes IPC para Login e Chat)

 chat-server/              -> Binário: chat-server.exe
    Cargo.toml
    src/
        main.rs
        channels/         (Canais de chat, LFG, Região, Whispers)
        net/              (Listener porta 10241)
        ipc/              (Listener IPC para GameServer)

 auto-start/               -> Binário: Auto-Start EmuRust.exe
    Cargo.toml
    src/
        main.rs
        supervisor/       (Gerenciamento de processos filhos, crash detection, restart)
        metrics/          (Coleta de CPU/RAM em tempo real via Windows API)
        logs/             (Roteamento, colorização e rotação de logs)
        ui/               (Interface gráfica moderna estilo macOS/iOS/Grafana)

 krypt/                    (Crate compartilhado de criptografia)
 bxml/                     (Crate compartilhado de leitura BXML)
 config/
     launcher.json         (Configuração central unificada)
```

## SOLUÇÃO
Configurar o `Cargo.toml` raiz como um workspace virtual gerenciando `login-server`, `game-server`, `chat-server`, `auto-start`, `krypt`, `bxml` e `pak`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/Cargo.toml`
* `Emulador-Rust/login-server/Cargo.toml`
* `Emulador-Rust/game-server/Cargo.toml`
* `Emulador-Rust/chat-server/Cargo.toml`
* `Emulador-Rust/auto-start/Cargo.toml`

## IMPLEMENTAÇÃO
* Edição do `Cargo.toml` raiz.
* Criação dos manifests `Cargo.toml` individuais.

## TESTES
* `cargo check --workspace`
* `cargo build --workspace --release`

## VALIDAÇÃO
* Workspace compila de ponta a ponta sem erros ou avisos de links quebrados.

## RISCOS
* Aumento do tempo de compilação inicial.
* Mitigação: Uso de compilação incremental e isolamento de dependências.

## DEPENDÊNCIAS
* Cargo workspace features.

## TO-DO
- [x] Desenhar a árvore de diretórios do workspace.
- [x] Configurar o Cargo.toml raiz.
- [x] Configurar crates `login-server`, `game-server`, `chat-server` e `auto-start`.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
