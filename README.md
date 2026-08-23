# Aion Classic EU — EmuRust (Emulador Rust de Alta Performance)

[![Rust](https://img.shields.io/badge/rust-stable-brightgreen.svg)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/status-Production%20Ready-success.svg)]()

O **EmuRust** é um emulador moderno em **Rust** voltado para o cliente de 64 bits do **Aion Classic EU (Gameforge)**. Projetado sob os princípios de modularidade do clássico emulador Java (4.8 Retail), o EmuRust implementa **3 servidores isolados** gerenciados por um único aplicativo supervisor com **Dashboard Gráfico moderno estilo macOS/iOS/Grafana**.

---

##  Arquitetura do Sistema

```text

                   AUTO-START EMURUST.EXE (GUI MANAGER)                   
                                                                          
  [ Dashboard Estilo macOS/iOS/Grafana | CPU/RAM | Logs Coloridos | JSON ]

                                     
         
          (Supervisão & Processos)   (Supervisão & Processos)   (Supervisão & Processos)
                                                               
                  
  LOGIN-SERVER               GAME-SERVER               CHAT-SERVER   
                                                                     
 • Auth Protocol  • World / Map    • Channels      
 • STS Protocol     IPC    • NPCs / Spawns    IPC    • Whispers      
 • Named Pipe     (Auth/   • Combat / Sys   (Sync/   • Client Socket 
 • Auto-Accounts  Session) • Entities       Verify)  • Lifecycle     
 • Brute-Force             • Inventory               • Sub-systems   
                  
```

---

##  Principais Recursos

1. **3 Servidores Totalmente Isolados**:
   * **`login-server`**: Unifica autenticação (portas `2106` e `13001`), protocolo STS (porta `6600`), Named Pipe Gameforge (`\\.\pipe\GameforgeClientJSONRPC`), auto-criação de contas e proteção anti-bruteforce.
   * **`game-server`**: Processo de mundo dedicado (porta `7777`, 20 TPS fixo) carregando **39.747 NPCs**, **76.693 Itens**, **11.476 Skills** e **1.254 Spawns**.
   * **`chat-server`**: Microserviço dedicado (porta `10241`) para canais regionais, LFG, comércio e whispers.

2. **Gerenciador Unificado `Auto-Start EmuRust.exe`**:
   * **Dashboard Gráfico**: Interface web moderna em `http://127.0.0.1:18080`.
   * **Métricas em Tempo Real**: Medição de CPU (%) e Memória (MB) por servidor via Windows API.
   * **Controles Granulares**: Ligar, parar e reiniciar servidores individualmente.
   * **Central de Logs Colorida**:
     *  **Login-Server**: Logs em Branco.
     * 🟢 **Game-Server**: Logs em Verde.
     *  **Chat-Server**: Logs em Ciano.
   * **Crash Detection & Auto-Restart**: Reinicia automaticamente processos que falharem.
   * **Rotação Diária com Retenção de 10 Dias**: Limpeza automática de arquivos antigos em `logs/`.

3. **Configuração Centralizada**:
   * Arquivo único `launcher.json` auto-documentado.

---

##  Como Iniciar o Emulador

### 1. Iniciar os Servidores
Abra a pasta `Produto Final/` e execute:
```text
Produto Final\Auto-Start EmuRust.exe
```
O painel do gerenciador será aberto automaticamente no seu navegador.

### 2. Iniciar o Cliente de Jogo
Na pasta do cliente, execute:
```text
Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
```

---

##  Estrutura do Repositório

```text
AionEMU/
 Produto Final/               # Pacote de produção pronto para rodar
    Auto-Start EmuRust.exe   # Gerenciador gráfico e supervisor
    login-server.exe         # Servidor de autenticação e STS
    game-server.exe          # Servidor de mundo e gameplay
    chat-server.exe          # Servidor de chat e canais
    aion.db                  # Banco de dados SQLite
    config/launcher.json     # Configuração centralizada
    data/                    # Dados de NPCs, Itens e Spawns
    logs/                    # Logs físicos diários com retenção

 Emulador-Rust/               # Código-fonte do emulador em Rust
    login-server/            # Crate do Login-Server
    game-server/             # Crate do Game-Server
    chat-server/             # Crate do Chat-Server
    auto-start/              # Crate do Supervisor e GUI
    commons/                 # Crate compartilhado de criptografia e utilitários

 PLANO-LOGINSERVER/           # 20 documentos do plano técnico de migração
 PLANO-DESENVOLVIMENTO/       # Memória técnica geral de desenvolvimento
 Cliente/                     # Cliente de jogo Aion Classic EU
 docs/                        # Documentação de protocolos e engenharia reversa
 CONTEXT.md                   # Manual técnico detalhado de offsets e opcodes
 README.md                    # Este arquivo
```

---

##  Compilação a partir do Código-Fonte

Requisitos:
* Rust 1.75+ (Cargo)
* Visual Studio 2022 com C++ Build Tools (MSVC x64)

```powershell
cd Emulador-Rust
cargo build --workspace --release
```

Os binários compilados estarão em `Emulador-Rust/target/release/`.
