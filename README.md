<div align="center">

<img src="Ferramentas e Documentos/Client e Coletas/Outros/Icones/AppTray2.png" alt="Aion Classic 5.0 Icon" width="140" height="140" />

# Aion Classic 5.0 EU — Servidor Emulador Oficial

<img src="Ferramentas e Documentos/Client e Coletas/Outros/Icones/Banner/splash_banner.png" alt="Aion Classic 5.0 Banner" width="100%" />

**Servidor Emulador de Alta Performance para Aion Classic 5.0 EU em Java 25 LTS e Painel Supervisor Nativo em Rust**

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
11. [Módulos Injetados no Cliente (BrService.dll e Version.dll)](#11-módulos-injetados-no-cliente-brservicedll-e-versiondll)
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
- **Módulos de Injeção e Extensão no Cliente (C/C++):** `version.dll` (proxy hook para bypass de autenticação e redirecionamento de conexões) e `BrService.dll` (overlay DirectX, HUD de latência, console Shugo, DPS meter, Combo UI e integração WebSocket).
- **Otimizador de Rota e Latência (C# / .NET 9):** `Academy NoLag`, subsistema de roteamento inteligente e tunelamento TCP/UDP para conexões competitivas de baixíssimo ping e eliminação de jitter.

---

## 2. Tecnologias e Versões

### Requisitos de Ambiente e Stack Tecnológica

| Componente | Tecnologia / Versão | Finalidade Técnica |
| :--- | :--- | :--- |
| **Linguagem Backend** | Java 25 LTS (`jdk-25.0.2`+) | Núcleo do servidor, Virtual Threads e Pattern Matching |
| **Gerenciador de Build Java** | Apache Maven 3.9+ | Compilação multimodular com `maven-compiler-plugin 3.14.1` |
| **Linguagem do Supervisor** | Rust 1.80+ (MSVC 64-bit) | Launcher nativo, supervisor de processos e Database Studio |
| **Compilador C/C++** | MSVC v143 (Visual Studio 2022) | Compilação nativa de `version.dll` e `BrService.dll` |
| **Plataforma .NET** | .NET 9.0 SDK | Compilação da suíte de tunelamento `Academy NoLag` |
| **Banco de Dados Relacional** | MySQL 8.x / MariaDB 10.x | Persistência segregada (`aion_ls`, `aion_cs`, `aion_gs`) |
| **Pool de Conexões** | HikariCP 7.0.2 | Gerenciamento de alta performance e resiliência de conexões |
| **Serialização & XML** | JAXB (Jakarta XML 2.3.3) + FastJSON2 | Parser de templates e intercâmbio de dados de alta velocidade |
| **Motor de Navegação** | CryEngine Native-Path (`*-path.dat`) | Resolução 0.5m tridimensional com 4 camadas de fallback |
| **Interface do Supervisor** | Wry 0.47 / Tao 0.31 (WebView2) | Dashboard gráfico acelerado por hardware |
| **Sistema Operacional** | Windows 10, 11 e Server (64-bit) | Ambiente de execução e compilação homologado |

---

## 3. Arquitetura da Solução

A solução adota arquitetura distribuída com microsserviços especializados comunicando-se em tempo real:

```
[ Cliente Aion Classic 5.0 (Gameforge) ]
         │
         ├─── (version.dll: Hook IAT + Redirecionamento 127.0.0.1)
         │
         ├───> Login Server (Porta 2106 TCP)
         │        ├── Handshake Criptográfico (RSA 1024-bit + Blowfish)
         │        ├── Autenticação de contas, GameGuard e Daeva Pass
         │        ├── Seleção de servidores e concessão de tokens de sessão
         │        └── Banco dedicado: aion_ls (8 tabelas)
         │
         ├───> Game Server (Porta 7777 TCP)
         │        ├── Particionamento Espacial e Instâncias 5.0 (Land of Shadows, etc.)
         │        ├── Movimento 3D e Pathfinding CryEngine (0.5m por célula)
         │        ├── Combate fluido, skills, status anormais e talentos de combate
         │        ├── Inventário, Wardrobe, Siel's Anvil/Hammer, Quna e Global Trade
         │        └── Banco dedicado: aion_gs (71+ tabelas)
         │
         ├───> Chat Server (Porta 10241 TCP)
         │        ├── Canais de chat global, região, sussurros, grupo e legião
         │        ├── Comandos administrativos de Game Master
         │        └── Banco dedicado: aion_cs (chatlog e auditoria)
         │
         └───> BrService.dll (Porta 10001 WebSocket)
                  ├── Overlay ImGui / DirectX (FPS, Latência, Radar 4-Eixos)
                  ├── Shugo Console administrativo in-game (Shift+F3 / Ctrl+X)
                  ├── DPS Meter em tempo real e Combo UI com partículas
                  └── Telemetria contínua com o GameServer
```

---

## 4. Estrutura do Código-Fonte e Distribuição

A estrutura de diretórios do repositório foi totalmente reorganizada, estabelecendo caminhos limpos, sem numerações legadas e com portabilidade absoluta:

```text
D:\AION CLASSIC 5.0 - EMULADOR\
│
├── Código Fonte - Emulador\                  # Backend Java 25 multimodular
│   ├── commons\                              # Núcleo de rede NIO, Blowfish/RSA, GeoIP e threads
│   ├── chat-server\                          # Servidor de chat, canais e moderação
│   ├── game-server\                          # Servidor de mundo, combate, IA, instâncias e itens
│   ├── login-server\                         # Servidor de autenticação e seleção de reinos
│   └── pom.xml                               # POM Maven agregador (release 25)
│
├── Emulador - Produto Final\                 # Distribuição de produção executável
│   ├── Aion Classic - EMULADOR.exe           # Supervisor e Launcher gráfico nativo (Rust)
│   ├── config.json                           # Parâmetros unificados de boot e JVM
│   ├── ChatServer\                           # Binários, libs, logs e sql do ChatServer
│   ├── GameServer\                           # Binários, libs, static_data e sql do GameServer
│   ├── LoginServer\                          # Binários, libs, logs e sql do LoginServer
│   └── WORLD IP RANGE\                       # Bases de prefixos IP para o Firewall GeoIP
│
└── Ferramentas e Documentos\                 # Hub consolidado de ferramentas e referências
    ├── Client e Coletas\                     # Coletas oficiais de rede e dados extraídos
    │   ├── Client 5.0 - Dados Extraidos\     # Dados canônicos do cliente (Levels, Data, etc.)
    │   ├── Outros\                           # Ícones oficiais e referências visuais
    │   │   └── Icones\                       # Ícones de bandeja e Banner oficial do Aion
    │   ├── Tradução - Português Brasil\      # Strings e textos traduzidos para PT-BR
    │   └── Wireshark - Oficial Classic 5.0\  # Capturas reais PCAPNG do tráfego oficial
    │
    ├── Códigos bin64\                        # Código-fonte C/C++ dos módulos do cliente
    │   ├── Código Fonte - BrService.dll\     # Overlay DirectX, ImGui, DPS Meter e Shugo Console
    │   └── Código Fonte - Version.dll\       # Hook IAT, No-IP, bypass GameGuard e DXVK
    │
    ├── Ferramentas Python e PowerShell\      # Suíte de desenvolvimento e otimização
    │   ├── Código Fonte - Academy NoLag\     # Otimizador de latência e roteamento (.NET 9)
    │   ├── Código Fonte - Executável Rust do Emulador\ # Código-fonte do supervisor Rust
    │   ├── Ferramentas Python\               # Decodificadores BXML, extratores PAK e utilitários
    │   └── parsersXML\                       # Suíte de geração e validação de static_data
    │
    └── Patch final - Client 5.0\             # Patch consolidado para aplicação no cliente
        ├── bin32\                            # DLLs compiladas de 32 bits
        ├── bin64\                            # DLLs compiladas de 64 bits (version.dll, BrService.dll)
        ├── l10n\                             # Localização e assets (BRA, ENG)
        ├── Start x64 - INGLÊS.bat            # Inicializador do cliente em inglês com flags
        └── Start x64 - PORTUGUÊS BRASIL.bat  # Inicializador do cliente em português com flags
```

---

## 5. Diretriz Mandatória de Clientes

> [!IMPORTANT]
> ### DIRETRIZ MANDATÓRIA DE CLIENTES:
> 1. **Cliente de Jogo e Desenvolvimento (`D:\GameForge\aionclassic`)**: É o cliente principal onde as DLLs compiladas (`version.dll`, `BrService.dll`), scripts `.bat` e arquivos de localização são aplicados para execução e testes práticos do emulador.
> 2. **Patch Consolidado (`Ferramentas e Documentos\Patch final - Client 5.0`)**: Contém a versão canônica e pronta para deploy de todos os arquivos de client que acompanham o emulador. Toda nova compilação das DLLs deve atualizar tanto esta pasta quanto a pasta do cliente de jogo.
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

| Serviço | Porta TCP | Protocolo | Descrição e Finalidade |
| :--- | :---: | :---: | :--- |
| **Login Server** | `2106` | Aion TCP | Porta padrão de autenticação, GameGuard e seleção de reinos. |
| **Game Server** | `7777` | Aion TCP | Porta principal do mundo, física, combate e instâncias. |
| **Chat Server** | `10241` | Aion TCP | Serviço de mensagens em tempo real, canais e comandos GM. |
| **BrService WebSocket** | `10001` | WS (RFC 6455) | Telemetria in-game, Shugo Console, Radar e DPS meter. |
| **Web Dashboard (Supervisor)**| `18080` | HTTP / WS | Painel web administrativo do inicializador Rust. |

---

## 9. Sistema de Proteção e Firewall GeoIP

O emulador integra nativamente no pacote `com.aionemu.commons.network.GeoIPFilterService` uma camada de proteção geográfica operando diretamente no socket NIO:

- **Bloqueio Prévio no Socket**: Rejeita imediatamente conexões de faixas IP fora dos países autorizados antes de alocar memória, decodificar pacotes ou iniciar handshakes.
- **Indexação em Memória**: Bases de dados de prefixos IPv4 e IPv6 (`WORLD IP RANGE/`) carregadas em memória para busca logarítmica instantânea.
- **Configuração Simples (`geo_firewall.properties`)**:
  - `geo.firewall.enable`: Ativa/desativa a filtragem geográfica (`true` / `false`).
  - `geo.firewall.allowed_countries`: Países liberados (ex: `BR,PT,US` ou `all`).
  - `geo.firewall.manual_whitelist_ips`: Lista de IPs individuais e sub-redes autorizadas para administração.
- **Fail-Safe Estrito**: Caso o firewall esteja ativado e os arquivos de faixas não possam ser lidos, a política de segurança fecha portas externas prevenindo invasões.

---

## 10. Subsistema de Navegação e Pathfinding (CryEngine Native-Path)

O emulador dispõe do motor primário tridimensional de alta resolução (`com.lostacademy.nativepath`), consumindo diretamente os arquivos de malha de navegação compilados da CryEngine (`*-path.dat`) extraídos das pastas de mapas do cliente oficial GameForge 5.0 (`Levels/`).

### Cadeia de 4 Camadas de Fallback:
1. **Camada 1: Native-Path (CryEngine `*-path.dat`)**:
   - Resolução ultraprecisa de 0.5m por célula.
   - Algoritmo A* heurístico tridimensional com fila de prioridade e suavização de trajetórias via *string-pulling raycasting*.
   - Suporte nativo a desníveis verticais, pontes, túneis e conexões de adjacência pré-calculadas.
2. **Camada 2: NavMesh (.nav Recast)**: Malhas trianguladas 3D carregadas sob demanda via `NavService` como primeira rota de contingência.
3. **Camada 3: Eleanor (Geometria / Line-of-Sight)**: Rastreamento dinâmico ponto a ponto via `FollowMotor` com checagens de linha de visão e desvio de obstáculos.
4. **Camada 4: Vanilla / Comportamento Direto**: Movimentação com ajuste de elevação Z via `GeoService.getZ`.

---

## 11. Módulos Injetados no Cliente (BrService.dll e Version.dll)

### 11.1 `version.dll` (Proxy Hook & Bypass)
- **No-IP Hook**: Intercepta as chamadas de socket do binário `Aion.bin`, redirecionando as conexões de rede oficiais para o emulador local (`127.0.0.1`), dispensando alterações manuais no arquivo `hosts` do Windows.
- **Bypass de GameGuard**: Neutraliza a checagem obrigatória do software anti-cheat proprietário, garantindo inicialização imediata e estável.
- **DXVK & Vulkan Fixes**: Compatibilização com camadas de renderização modernas, corrigindo travamentos de câmera e falhas de profundidade de pilha.

### 11.2 `BrService.dll` (Overlay DirectX & Shugo Console)
- **Controle via BAT**: Parâmetros modulares de inicialização (`-console`, `-freefly`, `-pingUi`, `-DpsMeterUI`, `-comboUi`, `-Model3D`, `-fov`, `-camMax`, `-fpsUnlock`, `-lang:BRA/ENG`).
- **Shugo Console Administrativo**: Acionado via atalhos **Shift + F3** ou **Ctrl + X**, com ajustes visuais de opacidade, escala e comandos rápidos de GM.
- **Combo UI Estilo LostHunting**: Mostrador de combos dinâmico com contagem de acertos, multiplicador de dano, partículas e banners temáticos.
- **Pontos de Participação**: A cada 1.000 acertos cumulativos em combate contra NPCs, o jogador recebe 1 Ponto de Participação persistido no banco de dados.
- **Radar de Combate 4-Eixos**: Substituídos os atributos genéricos; apresenta estritamente **Crítico**, **Bloqueio**, **Esquiva** e **Resistência**.
- **Gráfico Fibonacci de Latência**: Linha sutil renderizada abaixo do mostrador de MS com o histórico de oscilação dos últimos 60 minutos.
- **Ocultação Automática Inteligente**: O overlay se oculta instantaneamente quando a janela do Aion perde o foco ou é minimizada.

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

### 14.3 Compilando as DLLs do Cliente (MSVC)
```cmd
:: Compilação da Version.dll (x64 e x86)
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - Version.dll"
build.bat

:: Compilação da BrService.dll (x64)
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - BrService.dll"
Build64.bat
```
Ambos os scripts realizam a compilação e instalam os binários diretamente em:
- `Ferramentas e Documentos\Patch final - Client 5.0\bin64\`
- `D:\GameForge\aionclassic\bin64\`

---

## 15. Guia de Operação e Inicialização

### Inicialização do Servidor (Recomendado)
1. Navegue até a pasta `Emulador - Produto Final\`.
2. Execute o aplicativo `Aion Classic - EMULADOR.exe`.
3. O supervisor inicializa os serviços na sequência correta:
   - **Passo 1:** ChatServer (Porta 10241)
   - **Passo 2:** LoginServer (Porta 2106)
   - **Passo 3:** GameServer (Porta 7777)
4. Acesse o painel gráfico em tela para acompanhar métricas de memória, CPU, jogadores conectados ou abrir o Database Studio.

### Inicialização do Cliente de Jogo
1. Certifique-se de que o cliente em `D:\GameForge\aionclassic` possui as DLLs atualizadas.
2. Execute o inicializador do idioma desejado:
   - `Start x64 - PORTUGUÊS BRASIL.bat` (Cliente em Português)
   - `Start x64 - INGLÊS.bat` (Cliente em Inglês)
3. O cliente será iniciado com os módulos do emulador injetados, conectando-se diretamente ao servidor local.

---

## 16. Padrão Obrigatório de Commits

Para preservar a rastreabilidade e a consistência do repositório:

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, concisa, técnica e sem quebras desnecessárias.

---

## 17. Licença e Créditos

Este projeto foi desenvolvido com propósitos estritamente educacionais, de pesquisa acadêmica em sistemas distribuídos e de preservação histórica do jogo Aion Classic.

- **Desenvolvimento e Engenharia:** Equipe Aion Classic Emulator Project
- **Propriedade Intelectual Original:** Aion e Aion Classic são marcas registradas da NCSOFT Corporation e publicadas na Europa pela Gameforge 4D GmbH.
