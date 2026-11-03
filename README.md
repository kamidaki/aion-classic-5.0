<div align="center">

<img src="Ferramentas e Documentos/Client e Coletas/Outros/Icones/Banner/splash_banner.png" alt="Aion Classic 5.0" width="100%" />

# Aion Classic 5.0 — Emulador Oficial

**Emulador de Alta Performance para Aion Classic 5.0 EU em Java 25 LTS e Painel Supervisor Nativo em Rust**

[Repositório Oficial](https://github.com/kamidaki/aion-classic-5.0) | Versão: 5.0.0 Classic LTS | Arquitetura: Multimodular Java 25 + Rust Supervisor + CryEngine Native-Path

</div>

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Tecnologias e Versões](#2-tecnologias-e-versões)
3. [Arquitetura da Solução](#3-arquitetura-da-solução)
4. [Estrutura do Código-Fonte e Distribuição](#4-estrutura-do-código-fonte-e-distribuição)
5. [Diretriz Mandatória de Clientes](#5-diretriz-mandatória-de-clientes)
6. [Protocolo de Rede e Criptografia](#6-protocolo-de-rede-e-criptografia)
7. [Banco de Dados e Persistência](#7-banco-de-dados-e-persistência)
8. [Mapeamento de Portas e Serviços](#8-mapeamento-de-portas-e-serviços)
9. [Sistema de Proteção e Firewall GeoIP](#9-sistema-de-proteção-e-firewall-geoip)
10. [Subsistema de Navegação e Pathfinding (CryEngine Native-Path)](#10-subsistema-de-navegação-e-pathfinding-cryengine-native-path)
11. [Módulo Injetado no Cliente (Version.dll Standalone)](#11-módulo-injetado-no-cliente-versiondll-standalone)
12. [Otimizador de Latência (Academy NoLag - .NET 9)](#12-otimizador-de-latência-academy-nolag---net-9)
13. [Suíte de Ferramentas e Parsers XML](#13-suíte-de-ferramentas-e-parsers-xml)
14. [Compilação e Deploy](#14-compilação-e-deploy)
15. [Guia de Operação e Inicialização](#15-guia-de-operação-e-inicialização)
16. [Padrão Obrigatório de Commits](#16-padrão-obrigatório-de-commits)
17. [Licença e Créditos](#17-licença-e-créditos)

---

## 1. Visão Geral do Projeto

Este projeto é a implementação mais avançada, completa e moderna de um servidor emulador para o **Aion Classic 5.0 (versão europeia Gameforge)**, totalmente construído e operando em **Java 25 (LTS)**. O desenvolvimento é guiado por fidelidade absoluta ao cliente oficial, utilizando engenharia reversa sobre pacotes de rede (capturas Wireshark oficiais), tabelas extraídas diretamente do cliente 5.0 e inspeções de memória em tempo de execução.

O ecossistema divide-se em componentes perfeitamente orquestrados:

- **Camada de Backend (Java 25 LTS):** Composta por quatro módulos Maven (`commons`, `login-server`, `game-server`, `chat-server`), operando com Java Virtual Threads e Non-blocking I/O (NIO) de alto throughput, sem qualquer dependência legada do Javolution.
- **Camada de Supervisão e Launcher (Rust):** Executável nativo único compilado em código de máquina de 64 bits (`Aion Classic - EMULADOR.exe`), responsável pelo gerenciamento de ciclo de vida dos processos Java via Windows Job Objects, interface visual moderna em WebView2 (Edge Chromium), monitoramento de telemetria em tempo real e Database Studio embutido.
- **Módulos de Injeção e Extensão no Cliente (C/C++):** `version.dll` (proxy hook standalone de 64 e 32 bits para bypass de autenticação, No-IP, fixes de stack Windows 10/11, injeção de idioma PT-BR e correções de gameplay 5.0, operando de forma 100% independente e sem dependência de WebSocket) *(Nota: A DLL `BrService.dll` é experimental, foi completamente desativada, não é usada e nunca deve ser considerada).*
- **Otimizador de Rota e Latência (C# / .NET 9):** `Academy NoLag`, subsistema de roteamento inteligente e tunelamento TCP/UDP para conexões competitivas de baixíssimo ping e eliminação de jitter.

---

## 2. Tecnologias e Versões

### Requisitos de Ambiente e Stack Tecnológica

| Componente | Tecnologia / Versão | Finalidade Técnica |
| :--- | :--- | :--- |
| **Linguagem Backend** | Java 25 LTS (`jdk-25.0.2`+) | Núcleo do servidor, Virtual Threads e Pattern Matching |
| **Gerenciador de Build Java** | Apache Maven 3.9+ | Compilação multimodular com `maven-compiler-plugin 3.14.1` |
| **Linguagem do Supervisor** | Rust 1.80+ (MSVC 64-bit) | Launcher nativo, supervisor de processos e Database Studio |
| **Compilador C/C++** | MSVC v143 (Visual Studio 2022) | Compilação nativa de `version.dll` (proxy hook standalone) |
| **Plataforma .NET** | .NET 9.0 SDK | Compilação da suíte de tunelamento `Academy NoLag` |
| **Banco de Dados Relacional** | MySQL 8.x / MariaDB 10.x | Persistência segregada (`aion_ls`, `aion_cs`, `aion_gs`) |
| **Pool de Conexões** | HikariCP 7.0.2 | Gerenciamento de alta performance e resiliência de conexões |
| **Serialização & XML** | JAXB (Jakarta XML 2.3.3) + FastJSON2 | Parser de templates e intercâmbio de dados de alta velocidade |
| **Motor de Navegação** | CryEngine Native-Path (`*-path.dat`) | Motor autoritativo exclusivo 0.5m 3D com A* de alocação zero e Cache LRU |
| **Interface do Supervisor** | Wry 0.47 / Tao 0.31 (WebView2) | Dashboard gráfico acelerado por hardware |
| **Sistema Operacional** | Windows 10, 11 e Server (64-bit) | Ambiente de execução e compilação homologado |

---

## 3. Arquitetura da Solução

A solução adota arquitetura distribuída com microsserviços especializados comunicando-se em tempo real:

```text
[ Cliente Aion Classic 5.0 (Gameforge) ]
         |
         +---> (version.dll: Hook IAT + Suporte Multi-GameServer + Redirecionamento Dinâmico)
         |
         +---> Login Server (Porta 2106 TCP)
         |        +-- Handshake Criptografico (RSA 1024-bit + Blowfish)
         |        +-- Autenticacao de contas, GameGuard e Daeva Pass
         |        +-- Registro dinâmico de múltiplos GameServers (GSID 1, 2, 3)
         |        \-- Banco compartilhado: aionclassic_ls (8 tabelas)
         |
         +---> Chat Server (Porta 10241 TCP)
         |        +-- Gestão multi-GameServer concorrente (ConcurrentHashMap por GSID)
         |        +-- Canais de chat global, regiao, sussurros, grupo e legiao
         |        \-- Banco compartilhado: aionclassic_cs (1 tabela)
         |
         +---> GameServer 1: GameForge (GSID 1 | Porta 7777 TCP | Telemetria 2130)
         |        +-- Experiência original GameForge 5.0 oficial
         |        \-- Banco isolado: aionclassic_gs (86 tabelas)
         |
         +---> GameServer 2: Remake (GSID 2 | Porta 7778 TCP | Telemetria 2131)
         |        +-- Modalidade Remake com progressão balanceada
         |        \-- Banco isolado: aionclassic_gs2 (86 tabelas)
         |
         +---> GameServer 3: BattleRoyale (GSID 3 | Porta 7779 TCP | Telemetria 2132)
         |        +-- Modo de sobrevivência e arenas PvP dinâmicas
         |        \-- Banco isolado: aionclassic_gs3 (86 tabelas)
         |
         \---> Web Engine / Supervisor Dashboard (Porta 18080 HTTP/WS)
                  +-- Painel Administrativo SaaS moderno com métricas em tempo real
                  +-- Orquestrador automatizado e sequencial de inicialização
                  +-- Preparação inteligente e migrations SQL idempotentes (__migration_history)
                  \-- Editor integrado de propriedades com backups automáticos (.bak)
```

> [!WARNING]
> **AVISO IMPORTANTE SOBRE A BrService.dll:**  
> A `BrService.dll` **NÃO É USADA** no ecossistema e **NÃO FAZ PARTE** da arquitetura em operação. Trata-se de uma DLL experimental que foi completamente **desativada** e **NUNCA DEVE SER USADA OU CONSIDERADA**. O único módulo nativo de injeção suportado e utilizado pelo cliente oficial é a `version.dll` operando em modo 100% standalone e sem qualquer dependência externa.

---

## 4. Estrutura do Código-Fonte e Distribuição

A estrutura de diretórios do repositório foi totalmente reorganizada, estabelecendo caminhos limpos, sem numerações legadas e com portabilidade absoluta:

```text
aion-classic-5.0/
|
+-- CODE_OF_CONDUCT.md                        # Código de Conduta da Comunidade Técnica
+-- CONTRIBUTING.md                           # Guia de Contribuição e 10 Regras de Pull Request
+-- CONTEXT.md                                # Diretrizes Mandatórias de Engenharia e Arquitetura
+-- LICENSE                                   # Licença de Pesquisa Educacional e Não Comercial
+-- README.md                                 # Documentação Principal do Projeto
+-- SECURITY.md                               # Política de Segurança e Arquitetura de Proteção
+-- SUPPORT.md                                # Política Estrita de Zero Suporte (AS-IS)
|
+-- Código Fonte - Emulador\                  # Backend Java 25 multimodular
|   +-- commons\                              # Núcleo de rede NIO, Blowfish/RSA, GeoIP e threads
|   +-- chat-server\                          # Servidor de chat, canais e moderação (Concurrent Multi-GS)
|   +-- game-server-gameforge\                # GameServer 1: GameForge (GSID 1, Porta 7777 - Standby)
|   +-- game-server-remake\                   # GameServer 2: Remake (GSID 2, Porta 7778 - Padrão Ativo)
|   +-- game-server-battleroyale\             # GameServer 3: BattleRoyale (GSID 3, Porta 7779 - Standby)
|   +-- login-server\                         # Servidor de autenticação e seleção de reinos
|   \-- pom.xml                               # POM Maven agregador (release 25)
|
+-- Emulador - Produto Final\                 # Distribuição de produção executável
|   +-- Aion Classic - EMULADOR.exe           # Supervisor e Launcher gráfico nativo (Rust)
|   +-- Config\                               # Diretório unificado de configurações, GeoIP e runtime
|   |   +-- config.json                       # Parâmetros de boot (Xms1G / Xmx4G, Remake Ativo)
|   |   +-- GeoIP\                            # Bases de prefixos IP para o Firewall GeoIP
|   |   \-- java-deployment\                  # Runtime Java 25 LTS compilado/embutido
|   +-- ChatServer\                           # Binários, libs, logs e sql do ChatServer
|   +-- GameServer-GameForge\                 # Instância GameForge oficial (Desligada por padrão)
|   +-- GameServer-Remake\                    # Instância Remake oficial (Ligada por padrão)
|   +-- GameServer-BattleRoyale\              # Instância BattleRoyale oficial (Desligada por padrão)
|   \-- LoginServer\                          # Binários, libs, logs e sql do LoginServer
|
\-- Ferramentas e Documentos\                 # Hub consolidado de ferramentas e referências
    +-- Client e Coletas\                     # Coletas oficiais de rede e dados extraídos
    |   +-- Client 5.0 - Dados Extraidos\     # Dados canônicos do cliente (Levels, Data, etc.)
    |   +-- Outros\                           # Ícones oficiais e referências visuais
    |   |   \-- Icones\                       # Ícones de bandeja e Banner oficial do Aion
    |   +-- Tradução - Português Brasil\      # Strings e textos traduzidos para PT-BR
    |   \-- Wireshark - Oficial Classic 5.0\  # Capturas reais PCAPNG do tráfego oficial
    |
    +-- Códigos bin64\                        # Códigos-fonte dos módulos nativos (Ghidra & REA MCP)
    |   +-- README.md                         # Documentação técnica e diretrizes de uso da pasta Códigos bin64
    |   +-- Código Fonte - Version.dll\       # Conector oficial Client-Emulador, bypass oficial e customs
    |   +-- Código Fonte - Game.dll\          # [INCOMPLETO - NUNCA USAR NO JOGO ATÉ 100% IDÊNTICA AOS 31 MB]
    |   +-- Código Fonte - Crysystem.dll\     # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - Cry3DEngine.dll\   # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryAnimation.dll\  # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryEntitySystem.dll\ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryFont.dll\       # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryInput.dll\      # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryMovie.dll\      # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryPhysics.dll\    # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryScriptSystem.dll\ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CrySoundSystem.dll\ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   \-- Código Fonte - BrService.dll\     # [DESATIVADO/EXPERIMENTAL] DLL experimental desativada (NUNCA USAR)
    |
    +-- Ferramentas Python e PowerShell\      # Suíte de desenvolvimento e otimização
    |   +-- Código Fonte - Academy NoLag\     # Otimizador de latência e roteamento (.NET 9)
    |   +-- Código Fonte - Executável Rust do Emulador\ # Código-fonte do supervisor Rust
    |   +-- Ferramentas Python\               # Decodificadores BXML, extratores PAK e utilitários
    |   \-- parsersXML\                       # Suíte de geração e validação de static_data
    |
    \-- Patch final - Client 5.0\             # Patch consolidado para aplicação no cliente
        +-- bin32\                            # DLLs compiladas de 32 bits (version.dll)
        +-- bin64\                            # DLLs compiladas de 64 bits (version.dll standalone)
        +-- l10n\                             # Localização e assets (BRA, ENG)
        +-- Start x64 - INGLÊS.bat            # Inicializador do cliente em inglês com flags
        \-- Start x64 - PORTUGUÊS BRASIL.bat  # Inicializador do cliente em português com flags
```

---

## 5. Diretriz Mandatória de Clientes

> [!IMPORTANT]
> ### DIRETRIZ MANDATÓRIA DE CLIENTES:
> 1. **Cliente de Jogo e Desenvolvimento (`D:\GameForge\aionclassic`)**: É o cliente principal onde os binários compilados (`version.dll`), scripts `.bat` e arquivos de localização são aplicados para execução e testes práticos do emulador.
> 2. **Patch Consolidado (`Ferramentas e Documentos\Patch final - Client 5.0`)**: Contém a versão canônica e pronta para deploy de todos os arquivos de client que acompanham o emulador. Toda nova compilação da `version.dll` atualiza tanto esta pasta quanto a pasta do cliente de jogo.
> 3. **Proibição de Caminhos Hardcoded**: Nenhum arquivo versionado no repositório (código Java, C++, Rust, Python, `.bat` ou `.md`) deve conter letras de disco rígido fixas (`C:\`, `D:\`). Todas as referências devem resolver os caminhos relativos à raiz do projeto.

---

## 6. Protocolo de Rede e Criptografia

A comunicação entre o cliente oficial do Aion Classic 5.0 e os servidores é estritamente aderente ao protocolo binário oficial:

### Enquadramento e Pacotes (Wire Protocol)
- **Cabeçalho de Frame:** 2 bytes com o tamanho total do pacote em Little-Endian (incluindo o cabeçalho).
- **Corpo Cifrado:** Composto por `[u16 opcode_fio][u8 staticServerPacketCode = 0x65][u16 checksum = ~opcode_fio][payload]`.
- **Criptografia Simétrica (Blowfish):** Inicializada pelo pacote `S_KEY` do servidor (11 bytes em claro). Os 4 bytes finais trazem a semente necessária para derivar a chave de 8 bytes do algoritmo Blowfish com encadeamento ECB/CBC.
- **Autenticação Segura (RSA):** O LoginServer envia chave pública RSA de 1024 bits no pacote `SM_INIT`, utilizada pelo cliente para criptografar usuário e senha no pacote `CM_LOGIN`.

### Transformação Canônica de Opcodes (GameServer 5.0)

A camada de rede aplica transformações lineares sobre os identificadores de pacote:

$$\text{DecOp}_{\text{Cliente}\to\text{Servidor}} = ((\text{WireOp} \oplus 0x36) - 0xC4) \pmod{0x10000}$$

$$\text{DecOp}_{\text{Servidor}\to\text{Cliente}} = ((\text{WireOp} \oplus 0xD4) - 0xC4) \pmod{0x10000}$$

---

## 7. Banco de Dados e Persistência

A persistência do Aion Classic 5.0 opera com segregação relacional estrita em **3 bancos de dados independentes**:

### 7.1 Banco de Login (`aion_ls` - 8 tabelas)
- `account_data`: Contas de usuários, senhas criptografadas SHA-1, nível de acesso (0=Player, 1=VIP, 2=GM, 3=Admin) e créditos.
- `account_time`: Registro de tempo de jogo acumulado e controle de subscrição.
- `account_login_history`: Auditoria detalhada de acessos com timestamps, IPs e MACs.
- `gameservers`: Registro dinâmico de GameServers autorizados, com status de população e limites.
- `banned_ip`, `banned_mac`, `banned_hdd`: Tabelas de segurança para banimento por rede ou hardware.
- `player_transfers`: Gerenciamento de transferências de personagens entre reinos.

### 7.2 Banco de Chat (`aion_cs` - 1 tabela)
- `chatlog`: Auditoria de mensagens em tempo real com identificação de remetente, destinatário, canal e coordenadas.

### 7.3 Banco de Jogo (`aion_gs` - 71+ tabelas)
- `players`: Informações completas de personagens (classe, nível, EXP, coordenadas X/Y/Z/H, título, vida, mana, DP, cubos).
- `inventory`: Inventário com 150+ slots, equipamentos, refinos, manastones e fusões de armas.
- `player_skills`: Habilidades aprendidas, estigmas ativos e tempos de recarga.
- `player_quests`: Missões em andamento, passos concluídos e dados de campanhas 5.0.
- `legions` e `legion_members`: Sistema completo de legiões, patentes, histórico, emblemas e armazém de guilda.
- **Sistemas 5.0 Exclusivos**:
  - `player_life_stats_sp_ep`: Gestão dos pontos de energia SP e EP introduzidos na expansão 5.0.
  - `siel_anvil` e `siel_hammer`: Sistema de forja e aprimoramento de equipamentos de Siel.
  - `combat_talent_rewards`: Árvore de talentos de combate e recompensas progressivas.
  - `blackcloud_goods`, `global_trade`, `quna`, `wardrobe`: Loja Nuvem Negra, Comércio Global e Guarda-Roupa cosmético.
  - `player_participation_points` e `player_hits`: Recompensas dinâmicas a cada 1.000 golpes em combate.

---

## 8. Mapeamento de Portas e Serviços

| Serviço / Instância | GSID | Porta Jogo | Porta Telemetria | Banco de Dados | Descrição e Finalidade |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Chat Server** | — | `10241` | — | `aionclassic_cs` | Mensagens em tempo real com suporte multi-servidor concorrente. |
| **Login Server** | — | `2106` | — | `aionclassic_ls` | Autenticação RSA/Blowfish e roteamento para GameServers. |
| **GameServer - GameForge** | `1` | `7777` | `2130` | `aionclassic_gs` | Modalidade Oficial GameForge 5.0 (Desligado por padrão, -Xms1G / -Xmx4G). |
| **GameServer - Remake** | `2` | `7778` | `2131` | `aionclassic_gs2` | Modalidade Remake (Ligado por padrão, -Xms1G / -Xmx4G). |
| **GameServer - BattleRoyale** | `3` | `7779` | `2132` | `aionclassic_gs3` | Modalidade BattleRoyale (Desligado por padrão, -Xms1G / -Xmx4G). |
| **Web Dashboard (Supervisor)**| — | `18080`+ | — | — | Painel administrativo SaaS nativo em Rust. |

---

## 9. Sistema de Proteção e Firewall GeoIP

O emulador integra nativamente no pacote `com.aionemu.commons.network.GeoIPFilterService` uma camada de proteção geográfica operando diretamente no socket NIO:

- **Bloqueio Prévio no Socket**: Rejeita imediatamente conexões de faixas IP fora dos países autorizados antes de alocar memória, decodificar pacotes ou iniciar handshakes.
- **Indexação em Memória**: Bases de dados de prefixos IPv4 e IPv6 (`Config/GeoIP/`) carregadas em memória para busca logarítmica instantânea.
- **Configuração Simples (`geo_firewall.properties`)**:
  - `geo.firewall.enable`: Ativa/desativa a filtragem geográfica (`true` / `false`).
  - `geo.firewall.allowed_countries`: Países liberados (ex: `BR,PT,US` ou `all`).
  - `geo.firewall.manual_whitelist_ips`: Lista de IPs individuais e sub-redes autorizadas para administração.
- **Fail-Safe Estrito**: Caso o firewall esteja ativado e os arquivos de faixas não possam ser lidos, a política de segurança fecha portas externas prevenindo invasões.

---

## 10. Subsistema de Navegação e Pathfinding (CryEngine Native-Path)

O emulador dispõe do motor primário e **autoritativo exclusivo** de navegação e física tridimensional (`com.lostacademy.nativepath`), consumindo diretamente os arquivos de malha compilados da CryEngine (`*-path.dat`) extraídos das pastas de mapas do cliente oficial GameForge 5.0 (`Levels/`).

### Destaques e Arquitetura do Subsistema:
- **Autoridade Exclusiva CryEngine**: Os arquivos `*-path.dat` constituem a única fonte da verdade de navegação, sem fallbacks para Eleanor ou NavMesh genérico em tempo de execução.
- **Elevação 3D Real Ancorada ao Terreno**: Integração direta com a altitude topográfica do `GeoService.getZ`, combinando camadas de terreno natural e estruturas sobrepostas (pontes, rampas, plataformas elevadas) com tolerância segura a desníveis e proteção contra `Float.NaN`.
- **Motor A* 3D de Alocação Zero (Zero-GC)**: Contexto de busca `ThreadLocal` reutilizável com min-heap binário primitivo e tabela hash aberta indexada por gerações ($O(1)$ reset). Elimina alocações de heap e boxing de primitivos por busca.
- **Cinemática e Validação Física Rigorosa**:
  - Limite de subida máxima (*step up*): 0.8m.
  - Limite de descida máxima (*drop down*): 1.8m.
  - Prevenção geométrica de corte de quinas (*anti-corner-cutting*).
  - Raycasting DDA tridimensional e alisamento de rota (*string-pulling*).
- **Tratamento Determinístico de Falhas**: Backoff de 1000ms após falhas de repath e cancelamento estrito de movimento (`abortMove()`) quando a linha de visão física estiver bloqueada, eliminando atravessamento de paredes e despenhadeiros.
- **Gerenciamento de Memória com Cache Bounded LRU**: Mantém até 25 mapas simultâneos na memória com contagem ativa de jogadores (`onPlayerEnterMap` / `onPlayerLeaveMap`) e rotina periódica de limpeza a cada 3 minutos, reduzindo o consumo de RAM em repouso de >2.5 GB para menos de 150 MB.

---

## 11. Módulos Nativos do Cliente (C/C++ — Códigos bin64)

### 11.1 Reconstrução da Suíte CryEngine (Crytek) via Ghidra & REA MCP
A pasta `Ferramentas e Documentos/Códigos bin64` contém o código-fonte C/C++ da suíte completa da CryEngine e da lógica de jogo referente ao **Aion Classic 5.0**, reconstruído e catalogado através de engenharia reversa avançada utilizando **Ghidra 12.1.4** e **REA MCP**:

> [!CAUTION]
> ### REGRA CRÍTICA PARA AS DLLS DA CRYTEK:
> 1. As DLLs da Crytek (`CrySystem.dll`, `Cry3DEngine.dll`, `CryAnimation.dll`, `CryEntitySystem.dll`, `CryFont.dll`, `CryInput.dll`, `CryMovie.dll`, `CryPhysics.dll`, `CryScriptSystem.dll`, `CrySoundSystem.dll`) **SÓ DEVEM SER USADAS quando for garantido que todo o seu conteúdo é 100% IDÊNTICO ao original, sem nenhum problema ou divergência**.
> 2. No cliente operacional (`D:\GameForge\aionclassic`), **DEVEM SER MANTIDAS AS DLLs ORIGINAIS** da pasta `bin64` oficial.

> [!WARNING]
> ### REGRA INVIOLÁVEL PARA A `Game.dll`:
> 1. A **`Game.dll` NÃO ESTÁ COMPLETA**: Embora possua o mapeamento das 1.977 classes RTTI e 1.833 VTables via Ghidra/REA MCP, a implementação interna e a lógica de baixo nível de seus **~31.8 MB** ainda não estão concluídas.
> 2. **NUNCA DEVE SER USADA NO CLIENTE OPERACIONAL**: Ela **NUNCA DEVE SER USADA** ou substituída na pasta de jogo até que esteja comprovadamente **100% IDÊNTICA À ORIGINAL** em todo o seu conteúdo compilado de ~31.8 MB. O cliente operacional deve continuar usando exclusivamente a `Game.dll` original intacta.

### 11.2 `version.dll` (Conector Client-Emulador & Hub Homologado de Customs)
A `version.dll` é o componente nativo ativo encarregado de viabilizar a comunicação do cliente com o emulador:
- **Ponte de Conexão com o Emulador**: Responsável exclusiva por conectar o cliente com o emulador. Realiza o **bypass de todos os sistemas de validação oficiais da NCSoft/Gameforge** (erros de servidor de autorização, No-IP) e redireciona as chamadas WinSock (`connect`, `inet_ntoa`, `lstrcpynA`, `gethostbyname`) para os serviços locais (`127.0.0.1:2106`, `127.0.0.1:7777`).
- **Hub Oficial para Implementação de Customs**: Por ser modular e manter os binários originais intactos, é o local correto e homologado para inserir customizações e patches de compatibilidade:
  - **Desbloqueio Gráfico 4K / Ultrawide**: Remove o bloqueio de resolução no `crysystem`, suportando até 4096×4096, e corrige flickering de shaders (`shader_fix`).
  - **Injeção de Idioma PT-BR**: Patch em memória para suporte à localização `BRA` e supressão de bloqueios regionais de país.
  - **Compatibilidade Windows 11 24H2+ (x64)**: Tratamento de exceções vetorizadas (VEH), alinhamento de stack e controle de afinidade para CPUs com 32+ threads.
  - **Gameplay Fixes 5.0**: Ajuste do saldo de Quna em tempo real (`quna_fix`) e correção do travamento do diálogo de desmonte com Martelo de Siel (`siel_hammer_fix`).
- **Operação 100% Standalone & Zero WebSocket**: Totalmente autônoma, sem exigir tokens proprietários de linha de comando ou dependência de servidores WebSocket secundários.

### 11.3 `BrService.dll` (DLL Experimental Desativada — NÃO UTILIZADA)
> [!CAUTION]
> **ESTA DLL ESTÁ DESATIVADA E NUNCA DEVE SER USADA OU CONSIDERADA.**
> A `BrService.dll` foi um módulo experimental que foi inteiramente **desativado e descontinuado**.
> O emulador e o cliente oficial `Aion.bin` **NÃO USAM, NÃO CARREGAM E NÃO DEPENDEM** da `BrService.dll`.
> O único módulo nativo suportado e homologado para conexão e customizações do cliente é a `version.dll`.

---

## 12. Otimizador de Latência (Academy NoLag - .NET 9)

O projeto inclui o **Academy NoLag**, um software complementar de aceleração de rede em C# / .NET 9:

- **Roteamento Inteligente**: Otimiza a pilha de rede TCP/IP do Windows através de ajustes de socket (`TCP_NODELAY`, desativação de algoritmos de contenção como Nagle, ajuste de buffer de envio/recebimento).
- **Tunelamento de Tráfego**: Canaliza pacotes de combate entre cliente e servidor, prevenindo perda de pacotes e reduzindo a latência para valores próximos ao ping físico real.
- **Suíte de Testes Automatizada**: Integração com testes de unidade e validação rigorosa de integridade de buffers.

---

## 13. Suíte de Ferramentas e Parsers XML

Localizada em `Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML`, a suíte é responsável por garantir a integridade dos dados estáticos:

- **Extração e Conversão BXML**: Decodifica arquivos binários de dados do cliente oficial (`client_strings`, `item_templates`, `npc_templates`, etc.) para formato XML aberto.
- **Sincronização 5.0**: Parsers dedicados para geração de tabelas de skills, itens, missões, campanhas, NPCs de Land of Shadows, comércio global e vestuário.
- **Validação XSD**: Scripts de verificação garantem que cada arquivo gerado cumpra estritamente os esquemas de validação do GameServer antes da compilação.

---

## 14. Compilação e Deploy

### 14.1 Compilando os Servidores Java (Maven)
```cmd
mvn -f "Código Fonte - Emulador/pom.xml" clean package -DskipTests
```
Os artefatos compilados serão gerados nas respectivas pastas `target/`:
- `commons/target/commons-4.8-SNAPSHOT.jar`
- `login-server/target/login-server-4.8-SNAPSHOT.jar`
- `game-server/target/game-server-4.8-SNAPSHOT.jar`
- `chat-server/target/chat-server-4.8-SNAPSHOT.jar`

### 14.2 Compilando o Executável Supervisor em Rust
```cmd
cd "Ferramentas e Documentos\Ferramentas Python e PowerShell\Código Fonte - Executável Rust do Emulador"
Build.bat
```
O script compila via `cargo build --release` e publica o executável automaticamente em `Emulador - Produto Final\Aion Classic - EMULADOR.exe`.

### 14.3 Compilando a DLL do Cliente (MSVC)
```cmd
:: Compilação da Version.dll Standalone (x64 e x86)
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - Version.dll"
build.bat
```
O script realiza a compilação limpa (x64 e x86) e instala os binários diretamente em:
- `Ferramentas e Documentos\Patch final - Client 5.0\bin64\` (e `bin32\`)
- `D:\GameForge\aionclassic\bin64\` (e `bin32\`)

*(Nota 1: Apenas a `version.dll` é aplicada ao cliente de jogo. A `Game.dll` reconstruída e os módulos da Crytek pertencem à suíte de engenharia reversa/laboratório e NUNCA devem ser implantados no cliente de jogo operacional até atingirem 100% de paridade idêntica comprovada com os binários originais).*  
*(Nota 2: A `BrService.dll` é uma DLL experimental desativada que NÃO é usada e nunca deve ser considerada).*

---

## 15. Guia de Operação e Inicialização

### Inicialização do Servidor (Recomendado)
1. Navegue até a pasta Emulador - Produto Final\.
2. Execute o aplicativo Aion Classic - EMULADOR.exe.
3. O supervisor orquestra a sequência segura de inicialização dos serviços:
   - **Passo 1:** ChatServer (Porta 10241)
   - **Passo 2:** LoginServer (Porta 2106)
   - **Passo 3:** GameServers Habilitados:
     - GameForge (GSID 1 | Porta 7777 | DB aionclassic_gs)
     - Remake (GSID 2 | Porta 7778 | DB aionclassic_gs2)
     - BattleRoyale (GSID 3 | Porta 7779 | DB aionclassic_gs3)
4. Acompanhe métricas em tempo real de CPU, memória formatada, console de eventos ao vivo e o Database Studio integrado.

### Inicialização do Cliente de Jogo
1. Certifique-se de que o cliente em D:\GameForgeionclassic possui os módulos e scripts atualizados.
2. Execute o inicializador do idioma desejado:
   - Start x64 - PORTUGUÊS BRASIL.bat (Cliente em Português)
   - Start x64 - INGLÊS.bat (Cliente em Inglês)
3. O cliente iniciará com a ersion.dll conectora, realizando a conexão ao LoginServer e disponibilizando a seleção de qualquer GameServer ativo.

---

## 16. Diretrizes Mandatórias de Isolamento entre GameServers

> [!CAUTION]
> **REGRAS INEGOCIÁVEIS DE ISOLAMENTO DE GAMESERVERS:**
> 1. **Identificação Prévia Obrigatória:** Antes de qualquer alteração ou leitura relacionada a um GameServer, é OBRIGATÓRIO validar em qual GameServer será efetuada a ação (game-server-gameforge, game-server-remake ou game-server-battleroyale). **É inaceitável ler ou alterar todos os GameServers genericamente.**
> 2. **Servidores Totalmente Isolados e Independentes:** Cada GameServer é um servidor 100% isolado e independente, possuindo sistemas, regras de negócio e mecânicas distintas.
> 3. **Proibição de Consulta Cruzada:** NUNCA corrigir um problema de um GameServer consultando outro GameServer, exceto quando isso for estritamente solicitado pelo usuário.
> 4. **Consulta Obrigatória ao Usuário:** Sempre pergunte ao usuário em qual servidor será feita a alteração caso não tenha sido explicitamente fornecido, mesmo sob permissão máxima de autonomia.
> 5. **Auditoria de Conclusão de Tarefa:** No encerramento de qualquer tarefa, confirme formalmente se não alterou ou excluiu arquivos de outros GameServers sem autorização.
> 6. **Serviços Compartilhados (chat-server, login-server, ersion.dll):** Devem ser arquitetados pensando sempre no funcionamento conjunto com cada GameServer isoladamente. Alterações nos GameServers para fins de compatibilização são permitidas única e exclusivamente para conectividade e comunicação, jamais para gameplay.
> 7. **Proibição de Commits Globais:** NUNCA subir alterações em todos os GameServers simultaneamente.

---

## 17. Contribuição e Validação com Evidências Oficiais (Ghidra & Wireshark)

> [!IMPORTANT]
> **PADRÃO DE EVIDÊNCIAS DE ENGENHARIA REVERSA:**
> - **Proibição de PRs sem Testes e Imagens:** Não são aceitos Pull Requests sem testes práticos e imagens/capturas comprovando o funcionamento real em execução.
> - **Validação no Servidor Oficial Gameforge:** Diferente de testes genéricos ou em ROMs, todo comportamento deve ser validado e comparado diretamente contra o **servidor oficial Aion Classic Gameforge**.
> - **Evidências Concretas Obrigatórias:** Inaceitável qualquer correção sem comprovação empírica de que os valores, tabelas e fluxos correspondem ao oficial.
> - **Ferramentas Mandatórias:** É obrigatório utilizar **Ghidra** (análise e descompilação de binários PE32+ de 64 bits em in64) e **Wireshark** (capturas reais de tráfego de rede) para confirmação de opcodes, offsets de memória e estruturas.
> - **Pull Requests Mínimos e Atômicos:** Cada Pull Request deve ser pequeno e conciso, com foco exclusivo em uma correção ou funcionalidade específica. Não misture múltiplos sistemas em um único PR.

---

## 18. Padrão Obrigatório de Commits

Para preservar a rastreabilidade e a consistência do repositório:

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, concisa, técnica e sem emojis.
- **Escopo no Prefixo**: Commits devem identificar explicitamente o componente ou servidor afetado (ex: ix(gameforge): ..., eat(remake): ..., ix(login-server): ...).

---

## 19. Licença e Créditos

Este projeto foi desenvolvido com propósitos estritamente educacionais, de pesquisa acadêmica em sistemas distribuídos e de preservação histórica do jogo Aion Classic.

- **Desenvolvimento e Engenharia:** Equipe Aion Classic Emulator Project
- **Propriedade Intelectual Original:** Aion e Aion Classic são marcas registradas da NCSOFT Corporation e publicadas na Europa pela Gameforge 4D GmbH.
