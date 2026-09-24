# Aion Classic 5.0 EU — Java Emulator (Java 25 LTS)

O **melhor e único emulador Aion Classic 5.0 do mundo**, totalmente construído e operando em **Java 25 (LTS)**. Projetado para máxima estabilidade, fluidez absoluta, ausência de gargalos de concorrência e alto throughput, integrando protocolos oficiais Gameforge, criptografia Blowfish/RSA, dados estáticos 5.0 extraídos diretamente do cliente oficial e subsistema nativo de Firewall GeoIP.

---

> [!CAUTION]
> # DIRETRIZES MANDATÓRIAS E REGRAS INEGOCIÁVEIS DE DESENVOLVIMENTO
> **ESTAS REGRAS SÃO ESTRITAMENTE OBRIGATÓRIAS PARA TODOS OS DESENVOLVEDORES E AGENTES DE IA NESTE PROJETO.**
> **QUALQUER VIOLAÇÃO OU WORKAROUND QUEBRA A ARQUITETURA E NÃO SERÁ TOLERADA.**

### 1. Portabilidade Absoluta e Proibição de Caminhos Hardcoded
* **Este repositório é compartilhado e executado em múltiplos ambientes, computadores, discos e sistemas operacionais.**
* **É TERMINANTEMENTE PROIBIDO fixar letras de unidade de disco (ex: `C:\`, `D:\`, `E:\`) ou caminhos absolutos locais em qualquer arquivo do projeto** (seja código Java, scripts Python, arquivos `.bat`, `.ps1`, `.json`, `.xml` ou documentos `.md`).
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
- **Estrutura Recomendada**:
  ```text
  Título resumido da entrega em português

  - modulo-modificado: descrição objetiva da primeira mudança
  - outro-modulo: descrição objetiva da segunda mudança
  - ui/docs: descrição objetiva da terceira mudança
  ```

---

## Firewall GeoIP e Proteção de Fronteiras (Anti-Intrusão)

O emulador conta com um sistema de alta segurança integrado ao núcleo de rede (`commons`), projetado para mitigar ataques DDoS, bots de varredura e conexões não autorizadas de regiões geográficas não permitidas.

### 1. Arquitetura do GeoIPFilterService
- **Localização**: `com.aionemu.commons.network.GeoIPFilterService` gerenciado por `com.aionemu.commons.configs.GeoFirewallConfig`.
- **Atuação no Socket**: O filtro atua no instante imediato da conexão TCP, antes de qualquer processamento de handshake ou alocação pesada de memória.
- **Estrutura em Memória**: Carrega árvores de busca de prefixos IP para faixas IPv4 e IPv6 mapeadas a códigos ISO 3166-1 alpha-2 de países.
- **Modo Fail-Safe**: Caso o firewall esteja habilitado e a base de dados não possa ser lida, o serviço adota política de segurança restrita (`DENY-ALL` para todos os IPs externos não locais).

### 2. Configurações (`geo_firewall.properties` ou propriedades de sistema)
| Propriedade | Padrão | Descrição Técnica |
| :--- | :---: | :--- |
| `geo.firewall.enable` | `false` | Habilita ou desabilita globalmente o filtro de países. |
| `geo.firewall.world_ip_range_dir` | *(vazio)* | Diretório com os arquivos de faixas de IP por país. |
| `geo.firewall.allowed_countries` | `all` | Lista separada por vírgulas de países autorizados (ex: `BR,PT,US`). Se `all`, permite todos. |
| `geo.firewall.manual_whitelist_ips` | *(vazio)* | Lista explícita de IPs/sub-redes autorizados que ignoram restrição geográfica (para administradores e nós de proxy). |

---

## Subsistema de Navegação e Pathfinding (CryEngine Native-Path)

O emulador adota como motor primário de navegação tridimensional o pacote `com.lostacademy.nativepath`, que consome diretamente os arquivos compilados da CryEngine (`*-path.dat`) extraídos das pastas `Levels/` do cliente oficial GameForge 5.0.

### 1. Cadeia de 4 Camadas de Fallback
```text
[Camada 1: Native-Path (CryEngine .dat)]
         │
         ▼ (falha / sem arquivo / desativado)
[Camada 2: NavMesh (.nav Recast)]
         │
         ▼ (falha / sem malha / desativado)
[Camada 3: Eleanor (Geometria / Raycast LoS)]
         │
         ▼ (falha / sem rota transitável)
[Camada 4: Vanilla / Comportamento Normal (GeoService direto)]
```

### 2. Características do Subsistema
- **Precisão Espacial**: Grade de resolução 0.5m por célula nativa da CryEngine.
- **Mapeamento 3D Completo**: Suporte nativo a camadas verticais (pontes, túneis e rampas) e conexões de adjacência pré-calculadas.
- **Algoritmo A***: Busca heurística 3D de alta performance com fila de prioridade e alisamento via *string-pulling raycasting*.
- **Gerenciamento de Memória LRU**: Indexação dinâmica por prefixo numérico `{worldId}_*`, carregamento assíncrono sob demanda na entrada de jogadores e liberação automática de mapas inativos (`NativePathData`).
- **Compatibilidade 5.0**: 118 mapas indexados diretamente do cliente oficial em `data/native-path/`.

---

## Estrutura Oficial de Diretórios do Projeto

```text
├── Código Fonte - Emulador/              # Código-fonte Java multi-módulo em Java 25 (LTS)
│   ├── commons/                          # Núcleo de rede (NIO), criptografia Blowfish/RSA, GeoIP e threads
│   ├── chat-server/                      # Servidor de chat e canais em tempo real
│   ├── game-server/                      # Motor do mundo, física, IA, combate, entidades, skills, itens
│   ├── login-server/                     # Autenticação RSA, seleção de servidores e sessões
│   └── pom.xml                           # POM Maven agregador (compilador Java 25)
├── Emulador - Produto Final/             # Distribuição de produção executável e pronta para uso
│   ├── Aion Classic - EMULADOR.exe       # Executável compilado do Supervisor e Inicializador nativo (Rust)
│   ├── config.json                       # Configurações do supervisor, JVM e parâmetros de inicialização
│   ├── ChatServer/                       # Servidor de chat em produção
│   ├── GameServer/                       # Servidor de jogo, static_data e logs em produção
│   ├── LoginServer/                      # Servidor de autenticação em produção
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

## Ambiente de Execução e Stack Tecnológica

- **Linguagem & Runtime**: **Java 25 (LTS)** nativo (`jdk-25.0.2` LTS).
- **Build Tool**: Apache Maven 3.9+ com `maven-compiler-plugin 3.14.1` (`release 25`).
- **Banco de Dados**: MySQL 8.x / MariaDB 10.x / MySQL 5.7+ (Pool HikariCP 7.0.2).
- **Serialização & XML**: JAXB (`jakarta.xml.bind-api 2.3.3` com `jaxb-impl 2.3.9`) e FastJSON2 2.0.60.
- **Logging**: SLF4J 2.0.16 com Logback 1.5.21.
- **Protocol Buffers**: Google Protobuf Java 4.31.1.
- **Agendamento**: Quartz Scheduler 2.5.1 com ThreadPoolManager de alta performance.

---

## Workflow de Compilação e Deploy

$$\mathbf{Código\ Fonte} \xrightarrow{\text{mvn clean package}} \mathbf{JARs\ Compilados} \xrightarrow{\text{Deploy}} \mathbf{Produto\ Final} \xrightarrow{\text{Aion\ Classic\ -\ EMULADOR.exe}} \mathbf{Servidores\ Ativos}$$

1. **Alterações de Código**: Feitas exclusivamente em `Código Fonte - Emulador`.
2. **Compilação**:
   ```bash
   mvn -f "Código Fonte - Emulador/pom.xml" clean package -DskipTests
   ```
3. **Distribuição dos Artefatos**:
   Copiar os JARs gerados em `target/` para `Emulador - Produto Final/<Server>/libs/`.
4. **Execução**:
   Iniciar o emulador através de `Emulador - Produto Final/Aion Classic - EMULADOR.exe`.
