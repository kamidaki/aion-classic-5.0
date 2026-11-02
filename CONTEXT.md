# Aion Classic 5.0 EU — Java Emulator (Java 25 LTS)

O **melhor e único emulador Aion Classic 5.0 do mundo**, totalmente construído e operando em **Java 25 (LTS)**. Projetado para máxima estabilidade, fluidez absoluta, ausência de gargalos de concorrência e alto throughput, integrando protocolos oficiais Gameforge, criptografia Blowfish/RSA, dados estáticos 5.0 extraídos diretamente do cliente oficial, subsistema nativo de Firewall GeoIP e motor de navegação tridimensional CryEngine Native-Path.

---

> [!CAUTION]
> # DIRETRIZES MANDATÓRIAS E REGRAS INEGOCIÁVEIS DE DESENVOLVIMENTO
> **ESTAS REGRAS SÃO ESTRITAMENTE OBRIGATÓRIAS PARA TODOS OS DESENVOLVEDORES E AGENTES DE IA NESTE PROJETO.**
> **QUALQUER VIOLAÇÃO OU WORKAROUND QUEBRA A ARQUITETURA E NÃO SERÁ TOLERADA.**

### 1. Portabilidade Absoluta e Proibição de Caminhos Hardcoded
* **Este repositório é compartilhado e executado em múltiplos ambientes, computadores, discos e sistemas operacionais.**
* **É TERMINANTEMENTE PROIBIDO fixar letras de unidade de disco (ex: `C:\`, `D:\`, `E:\`) ou caminhos absolutos locais em qualquer arquivo do projeto** (seja código Java, C++, Rust, scripts Python, arquivos `.bat`, `.ps1`, `.json`, `.xml` ou documentos `.md`).
* Todas as referências devem ser **estritamente relativas** ou dinamicamente resolvidas via raiz do projeto (ex: `Código Fonte - Emulador`, `Emulador - Produto Final`, `Ferramentas e Documentos`).
* **NUNCA FAZER WORKAROUND (GAMBIARRAS OU ATALHOS TEMPORÁRIOS).**
* O estado atual do projeto em **Java 25 LTS** é definitivo e consolidado. **NUNCA recupere arquivos, dados ou referências a versões legadas obsoletas**.
* Use exclusivamente as capturas de rede de `Ferramentas e Documentos/Client e Coletas/Wireshark - Oficial Classic 5.0/` e dados extraídos em `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/`.

---

### 2. A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador seguem rigorosamente a cadeia causal de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

> [!IMPORTANT]
> ### Princípios Inegociáveis de Engenharia:
> 1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
> 2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`Ferramentas e Documentos/Client e Coletas/Wireshark - Oficial Classic 5.0/`) ou dos dados extraídos do cliente oficial (`Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/`).
> 3. **Purga Completa do Javolution e Adoção Nativa Java 25**: Toda a stack do emulador utiliza coleções nativas do Java 25 (`java.util`, `java.util.concurrent`), eliminando por completo classes legadas (`javolution.*`) para máxima eficiência de memória e concorrência nativa.
> 4. **Sincronização Código-Fonte $\leftrightarrow$ Produto Final**: Sempre que uma alteração for realizada em `Código Fonte - Emulador`, deve-se compilar e sincronizar os respectivos arquivos em `Emulador - Produto Final`.

---

### 3. Regra Rígida de Dados XML — NUNCA Fazer Bypass de Código por Dados Faltantes
> [!WARNING]
> **É TERMINANTEMENTE PROIBIDO CRIAR BYPASS NO JAVA PARA SUPRIR FALTA DE DADOS ESTÁTICOS!**
> Quando não houver definição de item, NPC, monstros, magias, skills ou atributos nos XMLs:
> - **NÃO crie fallbacks hardcoded, valores mágicos fictícios ou pontes que ignoram os templates.**
> - **A ÚNICA abordagem correta e obrigatória é CORRIGIR OS XMLs.**
> - Todas as correções de XML devem ser feitas utilizando os scripts e utilitários em:
>   `Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML` e `Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/aion_bxml.py`
> - A fonte canônica de dados oficiais do cliente 5.0 está em:
>   `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data`
> - Os templates do Java devem permanecer sincronizados em:
>   `Código Fonte - Emulador/game-server/data/static_data`
>   e
>   `Emulador - Produto Final/GameServer/data/static_data`

---

### 4. Padrão Obrigatório de Commits

Para manter o histórico do repositório organizado, rastreável e padronizado entre os desenvolvedores:

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, de forma concisa, técnica e objetiva.

---

## Estrutura Oficial de Diretórios do Projeto

```text
+-- Código Fonte - Emulador/              # Código-fonte Java multi-módulo em Java 25 (LTS)
|   +-- commons/                          # Núcleo de rede (NIO), criptografia Blowfish/RSA, GeoIP e threads
|   +-- chat-server/                      # Servidor de chat e canais em tempo real
|   +-- game-server/                      # Motor do mundo, física, IA, combate, entidades, skills, itens
|   +-- login-server/                     # Autenticação RSA, seleção de servidores e sessões
|   \-- pom.xml                           # POM Maven agregador (compilador Java 25)
+-- Emulador - Produto Final/             # Distribuição de produção executável e pronta para uso
|   +-- Aion Classic - EMULADOR.exe       # Executável compilado do Supervisor e Inicializador nativo (Rust)
|   +-- Config/                           # Diretório unificado de configurações, GeoIP e runtime
|   |   +-- config.json                   # Configurações do supervisor, JVM e parâmetros de inicialização
|   |   +-- GeoIP/                        # Tabelas de prefixos IP por país do Firewall GeoIP
|   |   \-- java-deployment/              # Runtime Java 25 LTS compilado/embutido para execução determinística
|   +-- ChatServer/                       # Servidor de chat em produção (libs, logs, sql)
|   +-- GameServer/                       # Servidor de jogo em produção (libs, static_data, logs, sql)
|   \-- LoginServer/                      # Servidor de autenticação em produção (libs, logs, sql)
\-- Ferramentas e Documentos/             # Hub consolidado de ferramentas, DLLs, patch e documentação
    +-- Client e Coletas/                 # PCAPs oficiais, dados extraídos e referências canônicas
    |   +-- Client 5.0 - Dados Extraidos/ # Dados oficiais extraídos do cliente (levels, data, etc.)
    |   +-- Outros/                       # Assets visuais e ícones
    |   |   \-- Icones/                   # Ícones de bandeja e Banner oficial Aion Classic
    |   |       \-- Banner/               # Imagem splash_banner.png para documentação
    |   +-- Tradução - Português Brasil/  # Textos e traduções oficiais PT-BR
    |   \-- Wireshark - Oficial Classic 5.0/ # Capturas reais de tráfego de rede do cliente 5.0
    +-- Códigos bin64/                    # Suíte de módulos nativos reconstruídos (Ghidra & REA MCP)
    |   +-- README.md                     # Documentação e regras mandatórias de paridade da pasta bin64
    |   +-- Código Fonte - Version.dll/   # Conector Client-Emulador oficial, bypass oficial e hub de customs
    |   +-- Código Fonte - Game.dll/      # [INCOMPLETO - NUNCA USAR NO JOGO ATÉ 100% IDÊNTICA AOS 31 MB]
    |   +-- Código Fonte - Crysystem.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - Cry3DEngine.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryAnimation.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryEntitySystem.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryFont.dll/   # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryInput.dll/  # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryMovie.dll/  # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryPhysics.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CryScriptSystem.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   +-- Código Fonte - CrySoundSystem.dll/ # Reconstrução CryEngine 5.0 via Ghidra/REA [SÓ USAR SE 100% IDÊNTICA]
    |   \-- Código Fonte - BrService.dll/ # [DESATIVADA/EXPERIMENTAL] DLL experimental desativada (NUNCA usar ou considerar)
    +-- Ferramentas Python e PowerShell/  # Utilitários, scripts de dados, reduções de ping e inicializadores
    |   +-- Código Fonte - Academy NoLag/ # Sistema de roteamento inteligente e tunelamento de latência (.NET 9)
    |   +-- Código Fonte - Executável Rust do Emulador/ # Código-fonte Rust do supervisor e launcher nativo
    |   +-- Ferramentas Python/           # Decodificadores BXML, extratores PAK e analisadores de PCAP
    |   \-- parsersXML/                   # Suíte de parsers para geração e sincronização de static_data
    \-- Patch final - Client 5.0/         # Patch consolidado pronto para o cliente (bin32, bin64, l10n, Start scripts)
```

---

## Banco de Dados e Persistência (Segregação Relacional)

O emulador opera com separação estrita de persistência em **3 schemas independentes** (MySQL 8.x / MariaDB 10.x):

### 1. Banco do Login Server (`aion_ls`)
- **Tabelas (8)**:
  - `account_data`: Contas, hashes SHA-1, nível de permissão (0=Jogador, 1=VIP, 2=GM, 3=Admin) e créditos.
  - `account_time`: Registro de tempo online acumulado e dias de assinatura ativa.
  - `account_login_history`: Log de auditoria de acessos com IP, MAC e timestamps.
  - `gameservers`: Registro dinâmico de GameServers autorizados, IPs de bind e status de capacidade.
  - `banned_ip`, `banned_mac`, `banned_hdd`: Controle de segurança e banimentos por rede ou hardware.
  - `player_transfers`: Controle de migração de personagens entre servidores.

### 2. Banco do Chat Server (`aion_cs`)
- **Tabelas (1)**:
  - `chatlog`: Registro persistente de conversas de chat global, local, sussurros e canais para auditoria e moderação.

### 3. Banco do Game Server (`aion_gs`)
- **Tabelas (71+)**:
  - `players`: Dados de personagens (classe, gênero, nível, EXP, coordenadas mundiais X/Y/Z/H, HP, MP, DP, cubos).
  - `inventory`: Itens equipados e na mochila, slots, manastones, fusões e níveis de encantamento.
  - `player_skills`: Habilidades ativas e passivas, estigmas equipados e cooldowns.
  - `player_quests`: Missões em andamento, passos concluídos e dados de campanhas 5.0.
  - `legions` e `legion_members`: Guildas, cargos, direitos de armazém, brasões e histórico.
  - **Sistemas 5.0 Exclusivos**:
    - `player_life_stats_sp_ep`: Gestão dos pontos de energia SP e EP introduzidos na expansão 5.0.
    - `siel_anvil` e `siel_hammer`: Forja de Siel e aprimoramento especial de equipamentos.
    - `combat_talent_rewards`: Árvores de talentos de combate e marcos de recompensa.
    - `blackcloud_goods`: Loja Nuvem Negra e produtos disponíveis para resgate in-game.
    - `global_trade`: Sistema unificado de comércio global entre jogadores.
    - `quna`: Carteira de moedas Quna e saldo de transações da loja.
    - `wardrobe`: Guarda-roupa cosmético 5.0 (slots desbloqueados e skins equipadas).
    - `player_participation_points` e `player_hits`: Concessão de 1 Ponto de Participação a cada 1.000 acertos em NPCs.

### 4. Inicialização e Migração Automática
- **Rust Database Manager**: O executável supervisor nativo possui rotina embutida que valida a existência dos bancos `aion_cs`, `aion_ls` e `aion_gs`, executando automaticamente os scripts SQL caso as tabelas ainda não existam.
- **Java DatabaseSchemaService**: O GameServer valida e cria dinamicamente novas tabelas ou colunas necessárias em tempo de boot, garantindo que o servidor nunca falhe por ausência de tabelas recentes.

---

## Mapeamento de Portas e Serviços de Rede

| Porta TCP | Serviço Responsável | Protocolo | Descrição Técnica |
| :---: | :--- | :---: | :--- |
| **2106** | LoginServer | Aion TCP | Porta primária de autenticação, validação GameGuard e seleção de reinos. |
| **7777** | GameServer | Aion TCP | Porta do mundo, combate, movimentação, instâncias e sincronização de entidades. |
| **10241** | ChatServer | Aion TCP | Serviço de comunicação em tempo real, canais e comandos de GM. |
| **8080** | Cloud Web Engine | HTTP / WS | Gateway Aion Cloud Port, runtime WebGL2 e WebSockets. |
| **18080** | Rust Supervisor | HTTP / WS | Painel web administrativo do inicializador (`Aion Classic - EMULADOR.exe`). |

---

## Arquitetura de Módulos Nativos do Cliente (C/C++ — Códigos bin64)

### 1. Reconstrução da Suíte CryEngine (Crytek) via Ghidra & REA MCP
A pasta `Ferramentas e Documentos/Códigos bin64` abriga os códigos-fonte da CryEngine e da lógica de jogo referente ao Aion Classic 5.0 obtidos por engenharia reversa via **Ghidra 12.1.4** e **REA MCP**:
- **Regra Estrita para Módulos Crytek**: O desenvolvedor ou agente de automação **SÓ DEVE USAR qualquer DLL reconstruída da Crytek quando garantir que 100% de seu conteúdo é IDÊNTICO ao original, sem divergências**. No cliente de jogo operacional (`D:\GameForge\aionclassic`), **devem ser mantidas as DLLs originais** da pasta `bin64`.
- **Regra Inviolável para a `Game.dll`**: A `Game.dll` **NÃO ESTÁ COMPLETA**. Apesar da catalogação de suas 1.977 classes RTTI e 1.833 VTables, as rotinas de seus **~31.8 MB** não estão finalizadas. Ela **NUNCA DEVE SER USADA** ou colocada no cliente operacional até paridade 100% comprovada com o binário original de 31.8 MB.

### 2. `version.dll` (Conector Client-Emulador & Hub Homologado de Customs)
- **Mecanismo e Conexão**: Carregada automaticamente pelo binário do cliente `Aion.bin` via técnicas de proxy DLL de sistema (`version.dll`). É a **responsável exclusiva por conectar o cliente oficial ao emulador**, realizando o bypass de validações e servidores oficiais (NCSoft / Gameforge) e direcionando as conexões WinSock para `127.0.0.1:2106` e `127.0.0.1:7777`.
- **Hub Homologado de Customizações ("Customs")**: É o ponto arquitetural correto para implementar melhorias e customizações sem violar os binários originais:
  - **Hook No-IP**: Intercepta a API WinSock (`connect`, `inet_ntoa`, `lstrcpynA`, `gethostbyname`), redirecionando silenciosamente chamadas para IPs externos para o emulador local (`127.0.0.1`) e tráfego HTTP/Shop para `127.0.0.1:8080`.
  - **Injeção de Idioma PT-BR & Bypass de País**: Patch dinâmico de tabelas de idioma em módulos CryEngine para habilitar `BRA` e neutralizar restrições regionais.
  - **Compatibilidade e Estabilidade Gráfica**: Desbloqueio de resolução até 4096×4096 no `crysystem`, correção de flickering de shaders, correção de afinidade de CPU para processadores com 32+ cores e correção de stack x64/VEH no Windows 11 (24H2+).
  - **Gameplay Fixes 5.0**: Interceptor de exibição de saldo de Quna (`quna_fix`) e correção do diálogo de resultado de desmonte de itens (`siel_hammer_fix`).
- **Independência Completa**: Opera de forma 100% autônoma, sem chamadas, carregamento ou acoplamento a `BrService.dll` e sem exigência de tokens proprietários ou sockets WebSocket secundários.

### 3. `BrService.dll` (DLL Experimental Desativada — NÃO UTILIZADA)
> [!CAUTION]
> **AVISO IMPORTANTE:** A `BrService.dll` **NÃO É USADA** no projeto.
> Trata-se de uma DLL experimental que foi completamente **desativada** e **NUNCA DEVE SER USADA OU CONSIDERADA**.
> O emulador e o cliente oficial `Aion.bin` não utilizam, não carregam e não possuem nenhuma dependência desta biblioteca. Toda a operação do cliente oficial é suportada exclusivamente pela `version.dll` de forma 100% autônoma.

---

## Subsistema de Navegação e Pathfinding (CryEngine Native-Path)

O emulador conta com um motor primário de navegação de alta fidelidade e resolução tridimensional (`com.lostacademy.nativepath`), consumindo diretamente os arquivos compilados da CryEngine (`*-path.dat`) extraídos das pastas de mapas do cliente oficial GameForge 5.0 (`Levels/`).

### Cadeia de 4 Camadas de Fallback:
1. **Camada 1: Native-Path (CryEngine `*-path.dat`)**:
   - Resolução ultraprecisa de 0.5m por célula.
   - Algoritmo A* heurístico tridimensional com fila de prioridade e suavização de trajetórias via *string-pulling raycasting*.
   - Suporte nativo a desníveis verticais, pontes, túneis e conexões de adjacência pré-calculadas.
2. **Camada 2: NavMesh (.nav Recast)**: Malhas trianguladas 3D carregadas sob demanda via `NavService` como primeira rota de contingência.
3. **Camada 3: Eleanor (Geometria / Line-of-Sight)**: Rastreamento dinâmico ponto a ponto via `FollowMotor` com checagens de linha de visão e detecção de obstáculos.
4. **Camada 4: Vanilla / Comportamento Direto**: Movimentação com ajuste de elevação Z via `GeoService.getZ`.

### Configuração (`geodata.properties`):
```properties
gameserver.nativepath.enable = true
gameserver.nativepath.dir = data/native-path/
gameserver.nativepath.max_cached_maps = 15
gameserver.nativepath.inactive_timeout_ms = 300000
gameserver.nativepath.cleanup_interval_ms = 180000
gameserver.nativepath.max_search_nodes = 4000
gameserver.nativepath.debug = false
```

---

## Firewall GeoIP & Proteção de Fronteiras

Integrado no pacote `com.aionemu.commons.network.GeoIPFilterService`:

1. **Bloqueio no Socket**: Conexões oriundas de faixas IP fora dos países autorizados são rejeitadas instantaneamente no nível NIO TCP antes do handshake de criptografia.
2. **Faixas IPv4 e IPv6**: Base de prefixos globais indexada em memória na inicialização.
3. **Configuração (`geo_firewall.properties`)**:
   - `geo.firewall.enable`: Ativa/desativa o firewall (`true` / `false`).
   - `geo.firewall.allowed_countries`: Países liberados (ex: `BR,PT,US` ou `all`).
   - `geo.firewall.manual_whitelist_ips`: IPs individuais autorizados que ignoram restrição geográfica.

---

## Arquitetura de Rede e Opcodes (Classic 5.0)

### 1. Fio de Rede (Wire Protocol) e Criptografia
- **Enquadramento**: `[u16 length (inclusive)][corpo cifrado]`
- **Corpo Cifrado**: `[u16 opcode_fio][1 byte staticServerPacketCode = 0x65][u16 checksum = ~opcode_fio][payload]`
- **Handshake Inicial**: Primeiro pacote do servidor é `S_KEY` (11 bytes em claro). Os 4 bytes finais trazem o seed para cálculo da chave Blowfish/XOR de 8 bytes.
- **Transformação Canônica de Opcodes (GameServer)**:
  - **Cliente $\to$ Servidor**:
    $$\text{decOp} = ((\text{wireOp} \oplus 0x36) - 0xC4) \pmod{0x10000}$$
  - **Servidor $\to$ Cliente**:
    $$\text{decOp} = ((\text{wireOp} \oplus 0xD4) - 0xC4) \pmod{0x10000}$$

---

### 2. Opcodes Canônicos: Login Server
| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x07` | `CM_AUTH_GG` | Handshake de integridade do GameGuard |
| C $\to$ S | `0x0B` | `CM_LOGIN` | Envio de credenciais criptografadas via RSA (Usuário/Senha) |
| C $\to$ S | `0x05` | `CM_SERVER_LIST` | Requisição da lista de servidores disponíveis |
| C $\to$ S | `0x02` | `CM_PLAY` | Seleção do servidor de jogo e solicitação de token |
| C $\to$ S | `0x08` | `CM_UPDATE_SESSION` | Sincronização de identificador de sessão ativa |
| C $\to$ S | `0x0E` | `CM_NP_LOGIN` | Autenticação unificada via token Web / Launcher |
| S $\to$ C | `0x00` | `SM_INIT` | Handshake inicial (Chave RSA + Chave Blowfish + Session ID) |
| S $\to$ C | `0x01` | `SM_LOGIN_FAIL` | Resposta de falha de autenticação |
| S $\to$ C | `0x02` | `SM_LOGIN_OK` | Confirmação de login com chaves `loginOk1` e `loginOk2` |
| S $\to$ C | `0x04` | `SM_SERVER_LIST` | Tabela oficial de servidores (ID, IP, Porta, Status, População) |
| S $\to$ C | `0x06` | `SM_PLAY_FAIL` | Notificação de erro na entrada de servidor |
| S $\to$ C | `0x07` | `SM_PLAY_OK` | Token de autorização para conexão ao GameServer |
| S $\to$ C | `0x0B` | `SM_AUTH_GG` | Validação positiva GameGuard |
| S $\to$ C | `0x0C` | `SM_UPDATE_SESSION` | Confirmação de sessão |

---

### 3. Opcodes Canônicos: Chat Server
| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x00` | `CM_CHAT_INI` | Inicialização da conexão TCP de chat |
| C $\to$ S | `0x05` | `CM_PLAYER_AUTH` | Autenticação do jogador com token do GameServer |
| C $\to$ S | `0x10` | `CM_CHANNEL_REQUEST` | Requisição de ingresso ou saída de canal de chat |
| C $\to$ S | `0x14` | `CM_CHANNEL_MESSAGE` | Envio de mensagem de texto para canal |
| S $\to$ C | `0x00` | `SM_CHAT_INI` | Resposta de inicialização do serviço de chat |
| S $\to$ C | `0x01` | `SM_PLAYER_AUTH_RESPONSE` | Validação da autenticação e liberação de canais |
| S $\to$ C | `0x11` | `SM_CHANNEL_RESPONSE` | Confirmação de entrada no canal |
| S $\to$ C | `0x15` | `SM_CHANNEL_MESSAGE` | Broadcast de mensagem de chat |

---

### 4. Opcodes Canônicos: Game Server (Classic 5.0)

#### Pacotes de Cliente $\to$ Servidor (`CM_*`)
| WireOp | DecOp | Nome do Pacote | Descrição / Payload |
| :---: | :---: | :--- | :--- |
| `0x00F2` | `0x0000` | `CM_VERSION_CHECK` | Verificação de versão de build do cliente 5.0 |
| `0x00E0` | `0x0012` | `CM_TIME_CHECK` | Sincronização de clock e ping do cliente |
| `0x00F1` | `0x0003` | `CM_QUIT` | Confirmação de desconexão graciosa |
| `0x00FE` | `0x0004` | `CM_MAY_QUIT` | Janela de contagem regressiva para saída |
| `0x0182` | `0x00F0` | `CM_L2AUTH_LOGIN_CHECK` | Autenticação de credenciais transferidas do LoginServer |
| `0x0114` | `0x005E` | `CM_CHARACTER_LIST` | Requisição de lista de personagens da conta |
| `0x0115` | `0x005F` | `CM_CREATE_CHARACTER` | Criação de novo personagem e customização visual |
| `0x01E9` | `0x011B` | `CM_DELETE_CHARACTER` | Marcação de personagem para exclusão |
| `0x011A` | `0x0058` | `CM_RESTORE_CHARACTER` | Cancelamento de exclusão de personagem |
| `0x00ED` | `0x0017` | `CM_CHARACTER_EDIT` | Modificação de aparência |
| `0x0143` | `0x00B1` | `CM_CHECK_NICKNAME` | Verificação de disponibilidade de apelido |
| `0x00EA` | `0x0018` | `CM_ENTER_WORLD` | Entrada no mundo de jogo com o personagem selecionado |
| `0x01A0` | `0x00D2` | `CM_CHARACTER_PASSKEY` | Autenticação da senha secundária de segurança |
| `0x0190` | `0x00E2` | `CM_AUTH_SUCCESS` | Notificação de sucesso de autorização |
| `0x01AC` | `0x00D6` | `CM_MAC_ADDRESS` | Envio de endereço físico e hardware ID |
| `0x00EB` | `0x0019` | `CM_LEVEL_READY` | Conclusão do carregamento de mapa/cena |
| `0x00E8` | `0x001A` | `CM_UI_SETTINGS` | Configurações locais de interface e atalhos |
| `0x00E9` | `0x001B` | `CM_CHAT_MESSAGE_PUBLIC` | Envio de mensagem de chat público |
| `0x00D6` | `0x001C` | `CM_CHAT_MESSAGE_WHISPER`| Envio de mensagem de chat privado |
| `0x00D2` | `0x0020` | `CM_ATTACK` | Desferimento de ataque básico físico |
| `0x00D3` | `0x0021` | `CM_CASTSPELL` | Execução ou canalização de magia/habilidade |
| `0x00D0` | `0x0022` | `CM_TOGGLE_SKILL_DEACTIVATE`| Desativação voluntária de skill toggle |
| `0x00D1` | `0x0027` | `CM_REMOVE_ALTERED_STATE`| Cancelamento voluntário de buff/aura |
| `0x00C7` | `0x002D` | `CM_USE_ITEM` | Consumo ou ativação de item do inventário |
| `0x00C4` | `0x002E` | `CM_EQUIP_ITEM` | Equipar ou desequipar item/arma |
| `0x00C2` | `0x0030` | `CM_MOVE` | Movimentação tridimensional e vetores de rotação |
| `0x00C3` | `0x0031` | `CM_MOVE_IN_AIR` | Voo livre ou navegação em Windstream |
| `0x00C0` | `0x0032` | `CM_QUESTION_RESPONSE` | Resposta a diálogo de confirmação/pergunta |
| `0x00C1` | `0x0033` | `CM_BUY_ITEM` | Compra/venda direta em NPC comerciante |
| `0x00CE` | `0x0034` | `CM_SHOW_DIALOG` | Abertura de diálogo com NPC |
| `0x00CD` | `0x0037` | `CM_TARGET_SELECT` | Seleção ou troca de alvo em mira |
| `0x00C8` | `0x003A` | `CM_GM_COMMAND_SEND` | Execução de comando administrativo |
| `0x00C9` | `0x003B` | `CM_EMOTION` | Execução de emote, descanso ou sentar |
| `0x0136` | `0x003C` | `CM_REMOVE_STIGMA`| Desequipar / remover pedra de estigma (4 bytes) |
| `0x01F3` | `0x0101` | `CM_GLOBAL_TRADE` | Comércio global unificado 5.0 |
| `0x0222` | `0x0150` | `CM_CLIENT_PING_STATE`| Heartbeat contínuo de latência do cliente |

#### Pacotes de Servidor $\to$ Cliente (`SM_*`)
| Opcode | Nome da Classe | Descrição / Payload |
| :---: | :--- | :--- |
| `0x0000` | `S_VERSION_CHECK` | Validação de protocolo e confirmação de build |
| `0x0001` | `S_STATUS` | Atributos gerais do personagem (HP, MP, DP, Ataque, Defesa) |
| `0x0003` | `S_HIT_POINT` | Atualização instantânea de pontos de vida |
| `0x0004` | `S_MANA_POINT` | Atualização instantânea de pontos de mana |
| `0x0008` | `S_EXP` | Atualização de pontos de experiência e nível |
| `0x000D` | `S_TUTORIAL_HINT` | Notificações contextuais de tutorial 5.0 |
| `0x000E` | `S_PUT_NPC` | Spawn de NPC no mundo com coordenadas e templates |
| `0x000F` | `S_WORLD` | Notificação de transição de mundo/mapa |
| `0x0014` | `S_REQUEST_TELEPORT` | Execução de teleporte de coordenadas |
| `0x0016` | `S_REMOVE_OBJECT` | Remoção de entidade da tela (despawn / distância) |
| `0x0018` | `S_MESSAGE` | Mensagem de sistema com texto livre |
| `0x0019` | `S_MESSAGE_CODE` | Mensagem de sistema via código estático de string |
| `0x001A` | `S_LOAD_INVENTORY` | Carga inicial do inventário com slots e itens |
| `0x0020` | `S_PUT_USER` | Spawn de outro jogador visível na tela |
| `0x0021` | `S_USE_SKILL` | Notificação de início de conjuração de magia |
| `0x0025` | `S_ACTION` | Efeitos de combate, golpes, acertos críticos e esquivas |
| `0x0027` | `S_SYNC_TIME` | Resposta de sincronização temporal de alta precisão |
| `0x0029` | `S_TARGET_INFO` | Informações do alvo (nível, vida, buffs visíveis) |
| `0x0031` | `S_ABNORMAL_STATUS` | Efeito de buff, debuff, veneno ou controle aplicado |
| `0x0033` | `S_LOAD_SKILL_COOLTIME` | Carga de tempos de recarga de habilidades |
| `0x0036` | `S_ATTACK` | Execução de animação de ataque físico |
| `0x0037` | `S_MOVE_NEW` | Atualização de posição e movimentação suave |
| `0x0047` | `S_KEY` | Handshake criptográfico oficial com chave Blowfish |
| `0x005F` | `S_ZONE_MAP_INFO` | Envio da geometria e dados vetoriais de mapas 5.0 |
| `0x0102` | `S_SECURITY_TOKEN` | Token de segurança secundário da sessão 5.0 |
| `0x0110` | `S_SEASON_PASS_INFO` | Informações de progresso do Season Pass / Daeva Pass |
| `0x0114` | `S_ACHIEVEMENT_REWARD_NOTI`| Notificações de conquistas completadas |
| `0x0133` | `S_ENTER_WORLD_CHECK` | Handshake confirmatório de entrada no mundo 5.0 |
| `0x019F` | `S_DAEVA_PASS_DATA` | Dados completos de missões e recompensas do Daeva Pass |

---

## Subsistema de Navegação e Pathfinding CryEngine (Native-Path)

O emulador adota o subsistema `com.lostacademy.nativepath` como motor **autoritativo e exclusivo** de navegação e física tridimensional dos NPCs, consumindo diretamente as malhas `*-path.dat` do cliente CryEngine oficial.

### Pilares Arquiteturais:
1. **Autoridade Canônica Exclusiva (Zero Eleanor / Zero NavMesh)**:
   - Os arquivos de navegação compilados CryEngine (`*-path.dat`) contêm nós de grade espacial com resolução de 0.5m, atributos de transitabilidade e camadas 3D originais do cliente.
   - Eliminados completamente fallbacks em tempo de execução para Eleanor ou NavMesh genérico Recast. Se não houver rota válida, o movimento é cancelado deterministicamente pela IA (`abortMove()`).
2. **Elevação Tridimensional Ancorada ao Terreno**:
   - `NativePathMap.getSurfaceZ` e `NativePathSector.findBestLayer` consultam a elevação topográfica real do `GeoService.getZ(worldId, x, y)` para calcular altitudes absolutas e relativas de camadas naturais e sobrepostas (pontes, túneis, estruturas).
   - Elimina o bug histórico de NPCs flutuando no ar ou afundando sob o relevo ao navegar em terreno inclinado.
3. **Motor A* 3D de Alocação Zero (Zero-GC Heap Churn)**:
   - Implementado via `ThreadLocal<AStarSearchContext>` com buffers primitivos planos (`long[]`, `float[]`, `int[]`).
   - Min-heap binário primitivo e tabela hash aberta com reset geracional em $O(1)$ (`generation` stamp).
   - Zero criação de objetos (`PriorityQueue`, `HashMap`, `HashSet`, boxing de `Long`/`Float`) por query de busca, eliminando centenas de MB/s de pressão de Garbage Collection em cenários de combate massivo.
   - Validações cinemáticas estritas: subida máxima de 0.8m, queda máxima de 1.8m, anti-corner-cutting e alisamento por raycasting DDA (*string-pulling*).
4. **Gerenciamento de Memória com Cache Bounded LRU**:
   - `NativePathData` gerencia o carregamento sob demanda com limite estrito de 25 mapas simultâneos no heap.
   - Rastreamento dinâmico de presença de jogadores (`onPlayerEnterMap` / `onPlayerLeaveMap`) e tarefa de limpeza periódica de mapas inativos a cada 3 minutos, reduzindo o uso de RAM de >2.5 GB para menos de 150 MB.
5. **Movimentação Determinística em `NpcMoveController`**:
   - Backoff determinístico de 1000ms após falhas no cálculo de rota, evitando recalcular A* desnecessariamente a cada tick.
   - Verificação física rigorosa via `NativePathService.canWalkDirectly` antes de qualquer movimento em linha reta, abortando a perseguição em vez de atravessar paredes ou obstáculos de colisão.

---

## Procedimento de Push para o Repositório Remoto (Resolução HTTP 408)

Em repositórios contendo conjuntos de dados de grande escala (como as pastas de extração do cliente com mais de 100.000 arquivos e 2.5 GB de dados já presentes no histórico remoto), a reorganização de pastas de nível raiz pode fazer com que o utilitário nativo `git pack-objects --revs` tente reempacotar todo o repositório histórico, gerando streams de 2.57 GB que ultrapassam o limite de tempo (timeout de ~120s) de requisições POST do GitHub (Erro `HTTP 408 Request Timeout`).

### Solução Canônica: Push Direto de Delta via Git Smart HTTP
Quando ocorrer essa situação:
1. Obtenha a lista exata dos objetos pendentes de envio entre o commit local e o commit remoto atual:
   ```cmd
   git rev-list --objects HEAD ^origin/main
   ```
2. Empacote estritamente esses objetos via `git pack-objects --stdout` (resultando em pacote compacto de ~4 MB).
3. Transmita o pacote diretamente ao endpoint `/git-receive-pack` utilizando o script utilitário em Python com credenciais do Git Credential Manager (`git credential fill`).
4. Atualize a referência local com `git update-ref refs/remotes/origin/main <HEAD>`.
