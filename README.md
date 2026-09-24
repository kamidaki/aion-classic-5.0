# Aion Classic 5.0 EU — Emulador Java (Java 25 LTS)

O **melhor e único emulador Aion Classic 5.0 do mundo**, totalmente construído e operando em **Java 25 (LTS)**. Desenvolvido com foco obsessivo em desempenho, estabilidade inabalável e fidelidade máxima ao cliente oficial **Aion Classic 5.0 (EU - Gameforge)**. Conta com compatibilização completa no protocolo de rede, criptografia Blowfish/RSA, sistema de combate fluido, dados estáticos 5.0 extraídos diretamente do cliente oficial e subsistema nativo de **Firewall GeoIP**.

---

## Destaques da Arquitetura 5.0

- **100% Java 25 (LTS)**: Compilado nativamente com javac release 25, aproveitando as mais modernas otimizações da JVM.
- **Purga Total do Javolution**: Substituição integral por coleções nativas de alta performance (`java.util` e `java.util.concurrent`), reduzindo overhead e consumo de heap.
- **Subsistema Native-Path CryEngine (4 Camadas de Navegação)**: Motor primário de pathfinding de altíssima fidelidade utilizando diretamente as malhas compiladas da CryEngine (`*-path.dat`) com resolução de 0.5m do cliente oficial GameForge 5.0, com fallback hierárquico para NavMesh (.nav Recast), Eleanor e Vanilla.
- **Firewall GeoIP Integrado**: Filtro geográfico nativo no socket NIO que bloqueia imediatamente conexões não autorizadas de países não permitidos antes de alocar memória ou processar pacotes.
- **Validação e Integridade Estática Completa**: Tabelas XML de skills, itens, NPCs, quests e motions 100% alinhadas com os esquemas XSD oficiais e dados extraídos do cliente 5.0.

---

## Estrutura de Diretórios do Projeto

```text
├── Código Fonte - Emulador/              # Código-fonte Java multi-módulo em Java 25 (LTS)
│   ├── commons/                          # Núcleo de rede (NIO), criptografia Blowfish/RSA, GeoIP e threads
│   ├── chat-server/                      # Servidor de chat e comunicação em tempo real
│   ├── game-server/                      # Motor de jogo, física, IA, combate, entidades, skills, itens
│   ├── login-server/                     # Autenticação RSA/Blowfish, seleção de servidores e sessões
│   └── pom.xml                           # POM Maven agregador multi-módulo (Java 25)
├── Emulador - Produto Final/             # Distribuição de produção executável e pronta para uso imediato
│   ├── Aion Classic - EMULADOR.exe       # Executável do Inicializador e Supervisor visual nativo (Rust)
│   ├── config.json                       # Configurações do inicializador, JVM e parâmetros de boot
│   ├── ChatServer/                       # Binários, libs e configurações do ChatServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   ├── LoginServer/                      # Binários e configs do LoginServer em produção
│   └── WORLD IP RANGE/                   # Tabelas de prefixos IP por país do Firewall GeoIP
└── Ferramentas e Documentos/             # Hub consolidado de ferramentas, DLLs, patch e documentação
    ├── Client e Coletas/                 # PCAPs oficiais, dados extraídos e referências canônicas
    │   ├── Client 5.0 - Dados Extraidos/ # Dados oficiais extraídos do cliente (skills, itens, npcs, strings)
    │   ├── Outros/                       # Ícones e referências complementares
    │   ├── Tradução - Português Brasil/  # Textos e traduções oficiais PT-BR
    │   └── Wireshark - Oficial Classic 5.0/ # Capturas reais de tráfego de rede do cliente 5.0
    ├── Códigos bin64/                    # Código-fonte C/C++ dos módulos nativos injetados no cliente
    │   ├── Código Fonte - BrService.dll/ # HUD de latência, Shugo console, DPS meter, Combo UI e WebSocket
    │   └── Código Fonte - Version.dll/   # Hook No-IP, bypass de auth, DXVK/Vulkan, fixes de câmera/stack
    ├── Ferramentas Python e PowerShell/  # Utilitários, scripts de dados, reduções de ping e inicializadores
    │   ├── Código Fonte - Academy NoLag/ # Sistema de roteamento inteligente e tunelamento de latência (.NET 9)
    │   ├── Código Fonte - Executável Rust do Emulador/ # Código-fonte Rust do supervisor e launcher nativo
    │   ├── Ferramentas Python/           # Decodificadores BXML, extratores PAK e analisadores de PCAP
    │   └── parsersXML/                   # Suíte de parsers para geração e sincronização de static_data
    └── Patch final - Client 5.0/         # Patch consolidado pronto para o cliente (bin32, bin64, l10n, Start scripts)
```

---

## Firewall GeoIP & Proteção Contra Países Não Autorizados

O emulador integra nativamente no pacote `com.aionemu.commons.network.GeoIPFilterService` uma camada de proteção geográfica e anti-intrusão operando no nível de transporte TCP:

1. **Bloqueio no Socket**: Conexões oriundas de faixas IP fora dos países autorizados são rejeitadas instantaneamente antes do handshake de criptografia, poupando CPU e memória do servidor.
2. **Faixas IPv4 e IPv6**: Base de dados de prefixos globais indexada em memória para busca em tempo logarítmico.
3. **Controle por Lista de Países**: Configuração simples por códigos ISO (ex: `BR,PT,US` ou `all` para liberar globalmente).
4. **Whitelist Manual**: Permite adicionar IPs ou sub-redes específicas para administradores e serviços parceiros.
5. **Configuração (`geo_firewall.properties` ou propriedades de sistema)**:
   - `geo.firewall.enable`: Ativa/desativa o firewall (`true` / `false`).
   - `geo.firewall.world_ip_range_dir`: Pasta com as tabelas de ranges IP por país.
   - `geo.firewall.allowed_countries`: Países liberados (ex: `BR,PT`).
   - `geo.firewall.manual_whitelist_ips`: IPs individuais autorizados.

---

## Subsistema de Navegação e Pathfinding (CryEngine Native-Path)

O emulador conta com um motor primário de navegação de alta fidelidade e resolução tridimensional (`com.lostacademy.nativepath`), consumindo diretamente os arquivos nativos de navegação compilados da CryEngine (`*-path.dat`) extraídos das pastas de mapas do cliente oficial GameForge 5.0 (`Levels/`).

### Cadeia de 4 Camadas de Fallback:
1. **Camada 1: Native-Path (CryEngine `*-path.dat`)**:
   - Resolução ultraprecisa de 0.5m por célula.
   - Algoritmo A* heurístico tridimensional com fila de prioridade e suavização de trajetórias via *string-pulling raycasting*.
   - Suporte nativo a desníveis verticais, pontes, túneis e conexões de adjacência pré-calculadas.
2. **Camada 2: NavMesh (.nav Recast)**:
   - Malhas trianguladas 3D carregadas sob demanda via `NavService` como primeira rota de contingência.
3. **Camada 3: Eleanor (Geometria / Line-of-Sight)**:
   - Rastreamento dinâmico ponto a ponto via `FollowMotor` com checagens de linha de visão e detecção de obstáculos.
4. **Camada 4: Vanilla / Comportamento Normal**:
   - Movimentação direta com ajuste de elevação Z via `GeoService.getZ`.

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

## A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador seguem rigorosamente a cadeia causal de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

### Princípios Inegociáveis de Engenharia:
1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`Ferramentas e Documentos/Client e Coletas/Wireshark - Oficial Classic 5.0/`) ou dos dados extraídos do cliente oficial (`Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/`).
3. **Sincronização Rigorosa**: Toda alteração no código-fonte em `Código Fonte - Emulador` deve ser compilada e os artefatos publicados em `Emulador - Produto Final`.

---

## Padrão Obrigatório de Commits

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, de forma concisa, técnica e objetiva.

---

## Compilação, Deploy e Inicialização

### 1. Compilação dos Servidores Java (Maven)
```bash
mvn -f "Código Fonte - Emulador/pom.xml" clean package -DskipTests
```
O build compila os módulos em Java 25 (`commons`, `chat-server`, `game-server`, `login-server`) e gera os `.jar` em cada pasta `target/`.

### 2. Deploy dos Binários no Produto Final
Copiar os artefatos gerados para a pasta de produção:
- `game-server/target/game-server-4.8-SNAPSHOT.jar` $\to$ `Emulador - Produto Final/GameServer/libs/`
- `commons/target/commons-4.8-SNAPSHOT.jar` $\to$ `Emulador - Produto Final/<Server>/libs/`
- `login-server/target/login-server-4.8-SNAPSHOT.jar` $\to$ `Emulador - Produto Final/LoginServer/libs/`
- `chat-server/target/chat-server-4.8-SNAPSHOT.jar` $\to$ `Emulador - Produto Final/ChatServer/libs/`

### 3. Como Iniciar o Emulador
A inicialização do emulador é realizada através do executável nativo único:
```text
Emulador - Produto Final\Aion Classic - EMULADOR.exe
```
Ao iniciar:
- Uma única instância do emulador é garantida via Windows Named Mutex.
- Os servidores são inicializados em ordem sequencial: **ChatServer** $\to$ **LoginServer** $\to$ **GameServer**.
- Todos os processos executam em segundo plano, com interface gráfica web integrada, telemetria de CPU/RAM em tempo real e Database Studio.

### 4. Conexão do Cliente Oficial 5.0
1. Tenha o cliente oficial **Aion Classic 5.0 (EU)** instalado.
2. Aplique os arquivos da pasta `Ferramentas e Documentos\Patch final - Client 5.0\` no diretório do seu cliente.
3. Inicie o jogo executando `Start x64 - PORTUGUÊS BRASIL.bat` ou `Start x64 - INGLÊS.bat`.

---

## BrService.dll & Recursos no Cliente

O patch do cliente inclui a **`BrService.dll`** (localizada em `bin64/`), que implementa recursos nativos modernos e integração em tempo real com o GameServer:

- **Controle Total via BAT**: Flags independentes no inicializador (`-console`, `-freefly`, `-pingUi`, `-DpsMeterUI`, `-comboUi`, `-Model3D`, `-fov`, `-camMax`, `-fpsUnlock`, `-lang:BRA/ENG`).
- **Console Shugo e Analisador de Combate**: Acionamento rápido via **Shift + F3** ou **Ctrl + X**, com ajustes visuais de opacidade, dimensões e modo compacto.
- **Combo UI Idêntico ao LostHunting**: Sistema de combos com contagem progressiva de hits, multiplicador de dano, pop scale, partículas e banners temáticos.
- **Pontos de Participação**: A cada 1.000 golpes cumulativos em combate contra NPCs agressivos, o jogador ganha 1 Ponto de Participação (persistido no banco de dados nas tabelas `player_participation_points` e `player_hits`).
- **Ajustes de Combo UI no Console**: Controle de opacidade, tamanho/escala e toggle de exibição (se ocultado, o ganho de pontos é pausado).
- **Radar de Combate 4-Eixos**: Substituídos os atributos genéricos; agora exibe estritamente **Crítico**, **Bloqueio**, **Esquiva** e **Resistência**.
- **Gráfico Fibonacci de Latência**: Linha fina branca desenhada abaixo do texto de MS, apresentando o histórico de subida/descida de latência dos últimos 60 minutos.
- **Disco / Emblema do Alvo**: Renderização fiel do disco/avatar de monstros e NPCs baseado na classificação oficial (`LEGENDARY`, `HERO`, `ELITE`, `NORMAL`) e raça (`ELYOS`, `ASMODIANS`).
- **Auto-criação de Tabelas no Banco**: Todas as tabelas SQL necessárias (`player_participation_points`, `player_hits`, `player_secure_area_log`, etc.) são criadas e validadas automaticamente na inicialização do GameServer via `DatabaseSchemaService`.
- **Ocultação Inteligente com Foco**: HUD de ping, console, gaveta e Combo UI se ocultam imediatamente quando a janela do Aion é minimizada ou perde o foco.
- **Pasta Sprites Localizada**: A pasta de sprites (`bin64/sprites/effects/`) é resolvida estritamente relativa à DLL, sem caminhos retrocessivos (`../`).

---

## Regras de Desenvolvimento e Qualidade
Consulte sempre o documento [`CONTEXT.md`](file:///CONTEXT.md) para conhecer as diretrizes obrigatórias de arquitetura, integridade de dados estáticos e fluxo de desenvolvimento canônico.

