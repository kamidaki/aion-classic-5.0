# Aion Classic 4.5 - Emulador em Rust (Alta Performance)

[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT%2FApache--2.0-blue.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-lightgrey.svg)]()
[![Version](https://img.shields.io/badge/Aion%20Client-Classic%204.5-red.svg)]()

Emulador de servidor de alta performance desenvolvido nativamente em **Rust** para **Aion Classic (Cliente versão 4.5 GameForge)**.

Repositório Oficial: [https://github.com/kamidaki/aion-classic-rust](https://github.com/kamidaki/aion-classic-rust)

---

## 🏛️ Estrutura do Repositório

O repositório é mantido limpo e organizado estritamente em duas frentes:

```
├── EmuRustDurak/            # CÓDIGO-FONTE RUST (Workspace & Crates)
│   ├── auth-server/         # Servidor de autenticação e lista de reinos (Blowfish/RSA)
│   ├── sts-server/          # STS Server (Handshake de segurança e tokens AES/RC4)
│   ├── game-server/         # Game Server (Mundo, combate, inventário, skills, SQLite)
│   ├── launcher/            # Emulador do Launcher oficial via Named Pipe
│   ├── krypt/               # Biblioteca compartilhada de cifras (XOR, RSA, RC4, AES)
│   ├── pak/ & bxml/         # Ferramentas de extração de dados .pak e binary XML
│   └── data/                # Dados estáticos (tabelas de spawn, itens e skills)
│
├── deploy/                  # EMULADOR DE PRODUÇÃO (Execução Limpa)
│   ├── auth-server.exe      # Binário de produção compilado
│   ├── sts-server.exe       # Binário de produção compilado
│   ├── game-server.exe      # Binário de produção compilado
│   ├── launcher.exe         # Binário de produção do launcher
│   ├── config.txt           # Configuração de IP, portas e caminho do cliente
│   ├── INICIAR_SERVIDOR.bat # Inicializador do servidor completo em 1 CLIQUE
│   ├── PARAR_SERVIDOR.bat   # Encerramento limpo de todos os processos em 1 CLIQUE
│   ├── iniciar.ps1          # Orquestrador PowerShell de produção
│   └── data/                # Dados estáticos essenciais de produção
│
├── PLANO-DESENVOLVIMENTO/   # ROTEIRO COMPLETO DE DESENVOLVIMENTO (22 Etapas)
├── scripts/                 # Scripts de automação (publicar_deploy.ps1)
├── CONTEXT.md               # Documento central de rastreamento de estado e progresso
└── README.md                # Este documento de referência
```

---

## 🚀 Como Iniciar o Emulador em 1 Clique (Produção)

Não é necessário ter o Rust ou compiladores instalados para executar o servidor na pasta `deploy/`:

1. Abra a pasta **`deploy/`**.
2. *(Opcional)* Edite o arquivo **`config.txt`** para definir o caminho do seu cliente e seu IP de rede (se deixado em branco, o IP da sua placa de rede será detectado automaticamente).
3. Dê um duplo-clique no arquivo **`INICIAR_SERVIDOR.bat`**.
   - O inicializador validará as portas, encerrará processos antigos e subirá os 3 servidores (`sts-server`, `auth-server` e `game-server`) em sequência.
   - Pressione **`L`** no terminal para disparar o cliente do jogo automaticamente.
4. Para parar o servidor, execute **`PARAR_SERVIDOR.bat`**.

---

## 🛠️ Como Compilar e Modificar o Código-Fonte (`EmuRustDurak`)

### Pré-requisitos:
- **Rust (Toolchain estável 1.80+)**: [rustup.rs](https://rustup.rs/)
- **Visual Studio 2022 / Build Tools C++** (com suporte a MSVC x64).

### Comandos de Compilação:
Abra o terminal no diretório `EmuRustDurak/`:

```powershell
# 1. Checagem rápida de tipos e compilação
cargo check --workspace

# 2. Executar testes unitários
cargo test --workspace

# 3. Compilar executáveis otimizados para produção (Release)
cargo build --release
```

---

## 📦 Como Publicar Atualizações na Pasta `deploy/`

Sempre que realizar alterações no código-fonte em Rust e validar o funcionamento, atualize a pasta de deploy executando:

```powershell
# A partir da raiz do projeto:
powershell -ExecutionPolicy Bypass -File scripts\publicar_deploy.ps1
```
Esse script compila o workspace em modo `--release` e copia automaticamente os novos binários (`.exe`) e dados atualizados para a pasta `deploy/`.

---

## 🗺️ Plano de Desenvolvimento Sequencial

O emulador segue uma arquitetura modular inspirada na estrutura consagrada do **Emulador Java 4.8 Retail**, adaptada para as funcionalidades e opcodes do **Aion Classic 4.5**.

Consulte a pasta [PLANO-DESENVOLVIMENTO/](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO) para acompanhar as 22 etapas numeradas:
- **Etapas 00 a 02**: Infraestrutura de Rede, Criptografia, STS, Auth e Criação de Personagens.
- **Etapas 03 a 06**: Motor de Mundo, Spatial Grid, GeoEngine, Atributos e Economia/Itens.
- **Etapas 07 a 11**: Combate (SkillEngine), IA de Monstros, Quests, Legiões/PvP e Instâncias.
- **Etapas 12 a 16**: Coleta/Crafting, Mascotes/Invocações, Habitações, Vento/Clima, Loja Web e Daeva Pass.
- **Etapas 17 a 21**: Agendamentos Cron, Sieges, Arenas, Anti-Hack, Mapeamento de Opcodes e Testes Autônomos.

---

## 🔄 Política de Versionamento no GitHub

> [!IMPORTANT]
> **Instrução para Agentes de IA e Desenvolvedores**:
> A cada marco técnico alcançado, bug corrigido ou etapa do plano concluída com sucesso:
> 1. Atualizar o arquivo [CONTEXT.md](file:///d:/AION%20RUST/AionEMU/AionEMU/CONTEXT.md).
> 2. Atualizar a pasta `deploy/` via `scripts/publicar_deploy.ps1`.
> 3. Realizar `git add .` e `git commit` com mensagem descritiva detalhando as mudanças para permitir rastreabilidade e facilitar rollbacks imediatos se necessário.
> 4. Realizar `git push` para o repositório remoto [https://github.com/kamidaki/aion-classic-rust](https://github.com/kamidaki/aion-classic-rust).
