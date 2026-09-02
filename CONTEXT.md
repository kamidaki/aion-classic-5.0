# Aion Classic 5.0 EU — Java Emulator

Emulador Java de alta performance para o cliente **Aion Classic 5.0 (EU - Gameforge)**, compatibilizado no protocolo de rede, handshake de criptografia Blowfish/RSA, opcodes 5.0, classes 5.0, tabelas estáticas de dados XML e arquitetura de compilação multi-módulo com Apache Maven.

---

> [!CAUTION]
> # 🚨 DIRETRIZES MANDATÓRIAS E REGRAS INEGOCIÁVEIS DE DESENVOLVIMENTO
> **ESTAS REGRAS SÃO ESTRITAMENTE OBRIGATÓRIAS PARA TODOS OS DESENVOLVEDORES E AGENTES DE IA NESTE PROJETO.**
> **QUALQUER VIOLAÇÃO OU WORKAROUND QUEBRA A ARQUITETURA E NÃO SERÁ TOLERADA.**

### 1. Portabilidade Absoluta e Proibição de Caminhos Hardcoded
* **Este repositório é compartilhado e executado em múltiplos ambientes, computadores, discos e sistemas operacionais.**
* **É TERMINANTEMENTE PROIBIDO fixar letras de unidade de disco (ex: `C:\`, `D:\`, `E:\`) ou caminhos absolutos locais em qualquer arquivo do projeto** (seja código Java, scripts Python, arquivos `.bat`, `.ps1`, `.json`, `.xml` ou documentos `.md`).
* Todas as referências devem ser **estritamente relativas** ou dinamicamente resolvidas via raiz do projeto (ex: `1 - Código Fonte [Emulador]`, `2 - Emulador [Produto Final]`, `4 - Patch para o Client 5.0`, `6 - Ferramentas`).
* **NUNCA FAZER WORKAROUND (GAMBIARRAS OU ATALHOS TEMPORÁRIOS).**
* O projeto é exclusivamente um **Emulador Java**. Qualquer referência a projetos ou emuladores legados deve ser tratada estritamente como histórico ou referência arquitetural quando expressamente solicitado (`5 - Documentação e Referências/3 - JAVA EMU - 4.8 RETAIL`).
* Use exclusivamente as capturas de rede de `5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/`.

---

### 2. A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador seguem rigorosamente a cadeia causal de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

> [!IMPORTANT]
> ### Princípios Inegociáveis de Engenharia:
> 1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
> 2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/`) ou da memória do processo do cliente em execução (`Aion.bin` / `game.dll`).
> 3. **Comparação e Encadeamento Limpo**: Comparar o comportamento identificado com as especificações canônicas do cliente, implementar apenas o necessário dentro da arquitetura desacoplada e garantir que não existam handlers duplicados, lógica espalhada ou soluções temporárias.

---

### 3. Regra Rígida de Dados XML — NUNCA Fazer Bypass de Código por Dados Faltantes
> [!WARNING]
> **É TERMINANTEMENTE PROIBIDO CRIAR BYPASS NO JAVA PARA SUPRIR FALTA DE DADOS ESTÁTICOS!**
> Quando não houver definição de item, NPC, monstros, magias, skills ou atributos nos XMLs:
> - **NÃO crie fallbacks hardcoded, valores mágicos fictícios ou pontes que ignoram os templates.**
> - **A ÚNICA abordagem correta e obrigatória é CORRIGIR OS XMLs.**
> - Todas as correções de XML devem ser feitas utilizando os scripts em:
>   `6 - Ferramentas/parsersXML`
> - Caso algum script Python da pasta de parsers esteja incompleto, **atualize o parser Python** para cobrir o que falta e gere novamente os dados.
> - A fonte de verdade dos dados oficiais do cliente 5.0 está localizada em:
>   `5 - Documentação e Referências/4 - Client 5.0 - Dados Extraidos/data`
>   É dessa pasta que os parsers extraem os dados oficiais e montam/comparam os XMLs de templates do Java em:
>   `1 - Código Fonte [Emulador]/GameServer/data/static_data`
>   e sincronizam com:
>   `2 - Emulador [Produto Final]/GameServer/data/static_data`

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

## 🏛 Arquitetura e Mapeamento Oficial de Opcodes (Classic 5.0)

### 1. Fio de Rede (Wire Protocol) e Matemática Criptográfica

- **Enquadramento**: `[u16 length (inclusive)][corpo cifrado]`
- **Corpo Cifrado**: `[u16 opcode_fio][1 byte staticServerPacketCode = 0x65][u16 checksum = ~opcode_fio][payload]`
- **Handshake Inicial**: Primeiro pacote do servidor é `S_KEY` (11 bytes em claro). Os 4 bytes finais trazem o seed para cálculo da chave Blowfish/XOR de 8 bytes.
  - `SUB_SEED = 0x3FF2CC87`
  - `XOR_SEED_32 = 0xCD92E451`
  - `XOR_SEED_64 = 0x87546CA100000000`

- **Transformação Canônica de Opcodes (GameServer)**:
  - **Cliente $\to$ Servidor**:
    $$\text{decOp} = ((\text{wireOp} \oplus 0x36) - 0xC4) \pmod{0x10000}$$
    $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0x36$$
  - **Servidor $\to$ Cliente**:
    $$\text{decOp} = ((\text{wireOp} \oplus 0xD4) - 0xC4) \pmod{0x10000}$$
    $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0xD4$$

---

### 2. Opcodes Canônicos: Login Server

| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x07` | `CM_AUTH_GG` | Handshake de integridade do GameGuard |
| C $\to$ S | `0x0B` | `CM_LOGIN` | Envio de credenciais criptografadas via RSA (Usuário/Senha) |
| C $\to$ S | `0x05` | `CM_SERVER_LIST` | Requisição da lista de reinos/servidores disponíveis |
| C $\to$ S | `0x02` | `CM_PLAY` | Seleção do servidor de jogo e solicitação de token |
| C $\to$ S | `0x08` | `CM_UPDATE_SESSION` | Sincronização de identificador de sessão ativa |
| C $\to$ S | `0x0E` | `CM_NP_LOGIN` | Autenticação unificada via token Web / Launcher |
| S $\to$ C | `0x00` | `SM_INIT` | Handshake inicial: Chave pública RSA + Chave Blowfish + Session ID |
| S $\to$ C | `0x01` | `SM_LOGIN_FAIL` | Resposta de falha de autenticação (código de erro e motivo) |
| S $\to$ C | `0x02` | `SM_LOGIN_OK` | Confirmação de login com chaves de sessão `loginOk1` e `loginOk2` |
| S $\to$ C | `0x04` | `SM_SERVER_LIST` | Tabela detalhada de servidores (ID, IP, Porta, Status, População) |
| S $\to$ C | `0x06` | `SM_PLAY_FAIL` | Notificação de erro na entrada de servidor (servidor cheio, etc.) |
| S $\to$ C | `0x07` | `SM_PLAY_OK` | Token de autorização para conexão ao GameServer (`playOk1`/`playOk2`) |
| S $\to$ C | `0x0B` | `SM_AUTH_GG` | Validação positiva do GameGuard |
| S $\to$ C | `0x0C` | `SM_UPDATE_SESSION` | Confirmação de sessão atualizada |

---

### 3. Opcodes Canônicos: Chat Server

| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x00` | `CM_CHAT_INI` | Inicialização de conexão TCP com o servidor de chat |
| C $\to$ S | `0x05` | `CM_PLAYER_AUTH` | Autenticação do jogador com token recebido do GameServer |
| C $\to$ S | `0x10` | `CM_CHANNEL_REQUEST` | Requisição de ingresso ou saída de canal de chat (LFG, Região, etc.) |
| C $\to$ S | `0x14` | `CM_CHANNEL_MESSAGE` | Envio de mensagem de texto para um canal de chat |
| S $\to$ C | `0x00` | `SM_CHAT_INI` | Resposta de inicialização do serviço de chat |
| S $\to$ C | `0x01` | `SM_PLAYER_AUTH_RESPONSE` | Validação da autenticação e liberação de canais |
| S $\to$ C | `0x11` | `SM_CHANNEL_RESPONSE` | Confirmação de entrada no canal com ID e atributos |
| S $\to$ C | `0x15` | `SM_CHANNEL_MESSAGE` | Broadcast de mensagem de chat para todos os membros do canal |

---

### 4. Opcodes Oficiais e Canônicos: Game Server

#### 4.1 Pacotes de Cliente $\to$ Servidor (`CM_*`) — Classic 5.0

| WireOp | DecOp | Nome do Pacote | Estado Válido | Descrição / Payload |
| :---: | :---: | :--- | :--- | :--- |
| `0x00F2` | `0x0000` | `CM_VERSION_CHECK` | `CONNECTED` | Checagem de versão de build do cliente 5.0 |
| `0x00E0` | `0x0012` | `CM_TIME_CHECK` | `CONNECTED`, `AUTHED`, `IN_GAME` | Sincronização de clock e ping do cliente |
| `0x00F1` | `0x0003` | `CM_QUIT` | `AUTHED`, `IN_GAME` | Confirmação de desconexão graciosa |
| `0x00FE` | `0x0004` | `CM_MAY_QUIT` | `AUTHED`, `IN_GAME` | Janela de contagem regressiva para saída |
| `0x0182` | `0x00F0` | `CM_L2AUTH_LOGIN_CHECK` | `CONNECTED` | Autenticação de credenciais transferidas do LoginServer |
| `0x0114` | `0x005E` | `CM_CHARACTER_LIST` | `AUTHED` | Requisição de lista de personagens da conta |
| `0x0115` | `0x005F` | `CM_CREATE_CHARACTER` | `AUTHED` | Criação de novo personagem e customização visual |
| `0x01E9` | `0x011B` | `CM_DELETE_CHARACTER` | `AUTHED` | Marcação de personagem para exclusão |
| `0x011A` | `0x0058` | `CM_RESTORE_CHARACTER` | `AUTHED` | Cancelamento de exclusão de personagem |
| `0x00ED` | `0x0017` | `CM_CHARACTER_EDIT` | `AUTHED` | Modificação de aparência via cupom |
| `0x0143` | `0x00B1` | `CM_CHECK_NICKNAME` | `AUTHED` | Verificação de disponibilidade de nome de personagem |
| `0x0179` | `0x008B` | `CM_MAY_LOGIN_INTO_GAME`| `AUTHED`, `IN_GAME` | Checagem de itens de conta e permissão de login |
| `0x00EA` | `0x0018` | `CM_ENTER_WORLD` | `AUTHED` | Entrada no mundo de jogo com o personagem selecionado |
| `0x01A0` | `0x00D2` | `CM_CHARACTER_PASSKEY` | `AUTHED` | Autenticação da senha secundária de segurança |
| `0x0190` | `0x00E2` | `CM_AUTH_SUCCESS` | `AUTHED`, `IN_GAME` | Notificação de sucesso de autorização |
| `0x01AC` | `0x00D6` | `CM_MAC_ADDRESS` | `CONNECTED`, `AUTHED`, `IN_GAME` | Envio de endereço físico e hardware ID da máquina |
| `0x00EB` | `0x0019` | `CM_LEVEL_READY` | `IN_GAME` | Conclusão do carregamento de mapa/cena pelo cliente |
| `0x00E8` | `0x001A` | `CM_UI_SETTINGS` | `IN_GAME` | Configurações locais de interface e atalhos |
| `0x00E9` | `0x001B` | `CM_CHAT_MESSAGE_PUBLIC` | `IN_GAME` | Envio de mensagem de chat público |
| `0x00D6` | `0x001C` | `CM_CHAT_MESSAGE_WHISPER`| `IN_GAME` | Envio de mensagem de chat privado (sussurro) |
| `0x00D2` | `0x0020` | `CM_ATTACK` | `IN_GAME` | Desferimento de ataque básico físico |
| `0x00D3` | `0x0021` | `CM_CASTSPELL` | `IN_GAME` | Execução ou canalização de magia/habilidade |
| `0x00D0` | `0x0022` | `CM_TOGGLE_SKILL_DEACTIVATE`| `IN_GAME` | Desativação voluntária de skill do tipo toggle |
| `0x00D1` | `0x0027` | `CM_REMOVE_ALTERED_STATE`| `IN_GAME` | Cancelamento voluntário de buff/aura |
| `0x00C7` | `0x002D` | `CM_USE_ITEM` | `IN_GAME` | Consumo ou ativação de item do inventário |
| `0x00C4` | `0x002E` | `CM_EQUIP_ITEM` | `IN_GAME` | Ação de equipar ou desequipar item/arma |
| `0x00C2` | `0x0030` | `CM_MOVE` | `IN_GAME` | Movimentação tridimensional e vetores de rotação |
| `0x00C3` | `0x0031` | `CM_MOVE_IN_AIR` | `IN_GAME` | Voo livre ou navegação em Windstream |
| `0x00C0` | `0x0032` | `CM_QUESTION_RESPONSE` | `IN_GAME` | Resposta a diálogo de confirmação/pergunta |
| `0x00C1` | `0x0033` | `CM_BUY_ITEM` | `IN_GAME` | Compra/venda direta em NPC comerciante |
| `0x00CE` | `0x0034` | `CM_SHOW_DIALOG` | `IN_GAME` | Abertura de diálogo com NPC |
| `0x00CD` | `0x0037` | `CM_TARGET_SELECT` | `IN_GAME` | Seleção ou troca de alvo em mira |
| `0x00CA` | `0x0038` | `CM_PLAYER_LISTENER` | `IN_GAME` | Rastreamento de objetos visíveis pelo jogador |
| `0x00C8` | `0x003A` | `CM_GM_COMMAND_SEND` | `IN_GAME` | Execução de comando administrativo |
| `0x00C9` | `0x003B` | `CM_EMOTION` | `IN_GAME` | Execução de emote, descanso ou sentar |
| `0x0136` | `0x003C` | `CM_BROKER_SEARCH` | `IN_GAME` | Pesquisa de itens no corretor de comércio |
| `0x0137` | `0x003D` | `CM_BROKER_REGISTERED_LIST`| `IN_GAME` | Listagem de itens registrados à venda |
| `0x0134` | `0x003E` | `CM_BUY_BROKER_ITEM` | `IN_GAME` | Compra de item no corretor de comércio |
| `0x0135` | `0x003F` | `CM_REGISTER_BROKER_ITEM` | `IN_GAME` | Registro de novo item à venda no corretor |
| `0x0132` | `0x0040` | `CM_EXCHANGE_ADD_ITEM` | `IN_GAME` | Inserção de item em troca entre jogadores |
| `0x0130` | `0x0042` | `CM_EXCHANGE_ADD_KINAH`| `IN_GAME` | Inserção de kinah em troca direta |
| `0x0131` | `0x0043` | `CM_EXCHANGE_LOCK` | `IN_GAME` | Travamento de segurança da janela de troca |
| `0x012F` | `0x0055` | `CM_EXCHANGE_CANCEL` | `IN_GAME` | Cancelamento voluntário de troca direta |
| `0x012E` | `0x0054` | `CM_EXCHANGE_OK` | `IN_GAME` | Confirmação final da transação |
| `0x00F5` | `0x0007` | `CM_EXCHANGE_REQUEST` | `IN_GAME` | Solicitação de troca para outro jogador |
| `0x012C` | `0x0056` | `CM_INIT_LEVEL` | `IN_GAME` | Requisição de dados da área ao trocar de mapa |
| `0x013D` | `0x0047` | `CM_PRIVATE_STORE` | `IN_GAME` | Abertura/fechamento de loja pessoal |
| `0x013C` | `0x0046` | `CM_OPEN_STATICDOOR` | `IN_GAME` | Interação de abertura com porta estática |
| `0x014C` | `0x00B6` | `CM_RECIPE_LIST` | `IN_GAME` | Requisição da árvore de receitas aprendidas |
| `0x01F3` | `0x0101` | `CM_GLOBAL_TRADE` | `IN_GAME` | Comércio global unificado 5.0 |
| `0x0222` | `0x0150` | `CM_CLIENT_PING_STATE`| `IN_GAME` | Heartbeat contínuo de latência do cliente |
| `0x03DC` | `0x0326` | `CM_SERVER_PVP_ACK` | `IN_GAME` | Confirmação de status e eventos de PvP |

#### 4.2 Pacotes de Servidor $\to$ Cliente (`SM_*`) — Destaques e Exclusivos 5.0

| Opcode | Nome da Classe | Descrição / Payload |
| :---: | :--- | :--- |
| `0x0000` | `S_VERSION_CHECK` | Validação de protocolo e confirmação de build |
| `0x0001` | `S_STATUS` | Atributos gerais do personagem (HP, MP, DP, Ataque, Defesa) |
| `0x0003` | `S_HIT_POINT` | Atualização instantânea de pontos de vida do jogador |
| `0x0004` | `S_MANA_POINT` | Atualização instantânea de pontos de mana do jogador |
| `0x0008` | `S_EXP` | Atualização de pontos de experiência e nível |
| `0x000D` | `S_TUTORIAL_HINT` | Dicas e notificações contextuais de tutorial 5.0 |
| `0x000E` | `S_PUT_NPC` | Spawn de NPC no mundo com coordenadas e templates |
| `0x000F` | `S_WORLD` | Notificação de transição de mundo/mapa |
| `0x0014` | `S_REQUEST_TELEPORT` | Execução de teleporte de coordenadas |
| `0x0016` | `S_REMOVE_OBJECT` | Remoção de entidade da tela (despawn / distância) |
| `0x0018` | `S_MESSAGE` | Envio de mensagem de sistema com texto livre |
| `0x0019` | `S_MESSAGE_CODE` | Envio de mensagem de sistema via código estático de string |
| `0x001A` | `S_LOAD_INVENTORY` | Carga inicial do inventário com slots, itens e blobs |
| `0x001B` | `S_ADD_INVENTORY` | Adição de novo item em slot específico |
| `0x001C` | `S_REMOVE_INVENTORY` | Remoção de item do inventário |
| `0x0020` | `S_PUT_USER` | Spawn de outro jogador visível na tela |
| `0x0021` | `S_USE_SKILL` | Notificação de início de conjuração de magia |
| `0x0024` | `S_WIELD` | Animação de desembainhar ou embainhar armas |
| `0x0025` | `S_ACTION` | Efeitos de combate, golpes, acertos críticos e esquivas |
| `0x0027` | `S_SYNC_TIME` | Resposta de sincronização temporal de alta precisão |
| `0x0029` | `S_TARGET_INFO` | Informações de alvo (nível, vida, buffs visíveis) |
| `0x002B` | `S_SKILL_SUCCEDED` | Confirmação de efeito aplicado por magia |
| `0x002C` | `S_ADD_SKILL` | Adição de nova magia aprendida à árvore de skills |
| `0x0031` | `S_ABNORMAL_STATUS` | Efeito de buff, debuff, veneno ou controle aplicado |
| `0x0033` | `S_LOAD_SKILL_COOLTIME` | Carga de tempos de recarga de todas as habilidades |
| `0x0036` | `S_ATTACK` | Execução de animação de ataque físico |
| `0x0037` | `S_MOVE_NEW` | Atualização de posição e movimentação suave |
| `0x0040` | `S_ITEM_LIST` | Lista de itens para janelas de diálogo e lojas |
| `0x0043` | `S_INVISIBLE_LEVEL` | Nível de invisibilidade / camuflagem do personagem |
| `0x0046` | `S_LOAD_WORKINGQUEST` | Carga das missões ativas em andamento |
| `0x0047` | `S_KEY` | Handshake criptográfico oficial com chave Blowfish de sessão |
| `0x005F` | `S_ZONE_MAP_INFO` | Envio da geometria e dados vetoriais de mapas 5.0 |
| `0x00A4` | `S_LOAD_GATHERCOMBINE_COOLTIME`| Tempos de recarga de coleta e extração |
| `0x00BC` | `S_LOAD_PVP_ENV` | Ambiente de PvP, pontuação e recompensas |
| `0x00D7` | `S_SKILL_PENALTY_STATUS` | Penalidades de uso excessivo ou falha de habilidade |
| `0x0102` | `S_SECURITY_TOKEN` | Token de segurança secundário da sessão 5.0 |
| `0x0105` | `S_ACCOUNT_REPUTATION` | Reputação de conta e pontuações do servidor |
| `0x0110` | `S_SEASON_PASS_INFO` | Informações de progresso do Season Pass / Daeva Pass |
| `0x0114` | `S_ACHIEVEMENT_REWARD_NOTI`| Notificações de conquistas completadas |
| `0x0133` | `S_ENTER_WORLD_CHECK` | Handshake confirmatório de entrada no mundo 5.0 |
| `0x0181` | `S_SERVER_TIME_EXP` | Bônus temporais de taxa de experiência do servidor |
| `0x019D` | `S_WORLD_ENV_FLAGS` | Flags climáticas e dinâmicas do mundo (UTF-16) |
| `0x019F` | `S_DAEVA_PASS_DATA` | Dados completos de missões e recompensas do Daeva Pass |
| `0x01C2` | `S_WARMUP_REPUTATION` | Sistema de aquecimento de reputação de combate |

---

## 🏛 Estrutura de Diretórios do Projeto

```text
├── 1 - Código Fonte [Emulador]/          # Código-fonte Java do Emulador (Login, Game, Chat)
│   ├── LoginServer/                      # Autenticação RSA/Blowfish, seleção de servidor e contas
│   ├── GameServer/                       # Mundo do jogo, física, entidades, skills, itens, dados estáticos
│   ├── ChatServer/                       # Canais de chat global, grupos e comunicação em tempo real
│   ├── pom.xml                           # POM Maven multi-módulo agregador
│   └── build-server.bat                  # Script de automação de compilação e deploy
├── 2 - Emulador [Produto Final]/         # Distribuição executável e pronta para execução imediata
│   ├── LoginServer/                      # Binários e configs do LoginServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   ├── ChatServer/                       # Binários e configs do ChatServer em produção
│   ├── StartAll.bat                      # Inicializador unificado de todos os serviços
│   └── StopAll.bat                       # Finalizador gracioso de todos os serviços
├── 2.5 - Executável Rust [Emulador]/     # Launcher/wrapper auxiliar de inicialização rápida
├── 3 - Código Fonte [Version.dll]/       # Hook C++/C# para o cliente (No-IP, bypass launcher oficial)
├── 4 - Patch para o Client 5.0/          # Patch pronto para o cliente (bin32, bin64, Start x64.bat)
├── 5 - Documentação e Referências/       # Documentações, PCAPs oficiais e dados de referência
│   ├── 1 - Backup Original do Version.dll (No-IP)
│   ├── 2 - Wireshark - Oficial Classic 5.0
│   ├── 3 - JAVA EMU - 4.8 RETAIL
│   ├── 4 - Client 5.0 - Dados Extraidos
│   └── 5 - PLANOS
└── 6 - Ferramentas/                      # Scripts de geodata, PCAP, análise de memória e parsers XML
    └── parsersXML/                       # Suíte completa de parsers XML 5.0 sincronizada com o client
```

---

## ⚡ Ambiente de Execução e Roadmap

- **Runtime Atual**: Java 8 (Recomendado: `jdk1.8.0_431` ou superior x64).
- **Build Tool**: Apache Maven 3.8+ (3.9.9 testado).
- **Banco de Dados**: MySQL 5.7+ / MariaDB 10.x / MySQL 8.x.
- **Roadmap Futuro**:
  - Migração planejada para **Java 25 (LTS)**.
  - Otimizações com Virtual Threads (Project Loom), Foreign Function & Memory API e alto throughput de concorrência.

---

## 🛠 Workflow de Desenvolvimento

$$\mathbf{Código\ Fonte\ [1]} \xrightarrow{\text{mvn clean package / build-server.bat}} \mathbf{Build\ &amp;\ Deploy} \xrightarrow{\text{Sincronização}} \mathbf{Produto\ Final\ [2]} \xrightarrow{\text{StartAll.bat}} \mathbf{Servidor\ Ativo}$$

1. **Alterações de Código**: Feitas exclusivamente em `1 - Código Fonte [Emulador]`.
2. **Compilação**: Executada via `build-server.bat` ou `mvn clean package -DskipTests=true`.
3. **Deploy**: O `build-server.bat` publica e atualiza automaticamente os artefatos em `2 - Emulador [Produto Final]`.
4. **Execução**: Realizada através de `StartAll.bat` dentro de `2 - Emulador [Produto Final]`.
