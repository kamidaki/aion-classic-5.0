<div align="center">

# Aion Classic 4.5 — Emulador Rust de Alta Performance

**O primeiro emulador do mundo para Aion Classic 4.5 escrito inteiramente em Rust**  
Desenvolvido do zero através de engenharia reversa do cliente oficial Gameforge Classic 4.5 x64 (`Aion.bin` / `game.dll`).

[![Rust](https://img.shields.io/badge/rust-stable-DEA584?logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/license-GPLv3-4E9A06)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-0078D6?logo=windows&logoColor=white)]()
[![Status](https://img.shields.io/badge/status-Production%20Ready-2EA44F)]()
[![Tests](https://img.shields.io/badge/tests-176%20passed%20100%25-brightgreen)]()
[![Origin](https://img.shields.io/badge/origem-Brasil-009C3B)]()

</div>

---

## Indice

1. [Visao Geral](#visao-geral)
2. [Regras Obrigatorias de Autenticacao e Login](#regras-obrigatorias-de-autenticacao-e-login)
3. [Roadmap do Projeto (Feitos e Pendentes)](#roadmap-do-projeto-feitos-e-pendentes)
4. [Arquitetura e Mapeamento de Opcodes](#arquitetura-e-mapeamento-de-opcodes)
5. [Painel Supervisor e Telemetria Day-Trade](#painel-supervisor-e-telemetria-day-trade)
6. [Login Server e Criptografia](#1-login-server)
7. [Game Server e Mundo](#2-game-server)
8. [Chat Server e Redes](#3-chat-server)
9. [Banco de Dados SQLite v2](#banco-de-dados-sqlite-v2)
10. [Como Iniciar o Emulador](#como-iniciar)
11. [Compilacao a partir do Codigo-Fonte](#compilacao-a-partir-do-codigo-fonte)

---

## Visao Geral

O **EmuRust** e uma reimplementacao nativa, em **Rust**, do ecossistema de servidor necessario para operar o cliente **Aion Classic EU (Gameforge)** em sua versao 4.5. Diferente dos emuladores tradicionais em Java, esta stack foi construida para entregar **zero microtravamentos (Zero Garbage Collection)**, consumo ocioso de 0.00% de CPU, tick rate cravado em 20.0 TPS e fidelidade absoluta byte a byte com as capturas oficiais de rede do Wireshark.

---

## Regras Obrigatorias de Autenticacao e Login

Seguindo o padrao consolidado dos emuladores privados consagrados de Aion (Java 4.8 Retail e Java 2.4 Classic Gameforge):

### 1. Autenticacao Pura por "Login & Senha"
* **Sem dependencias externas**: O login acontece **exclusivamente com usuario e senha**. Nenhuma autenticacao por Launcher externo, OAuth, 2FA, SMS ou codigo de telefone e necessaria.
* **Metodos opcionais desconsiderados**: Todos os metodos alternativos presentes nos binarios do cliente sao ignorados pelo emulador, mantendo o processo limpo, direto e compativel.

### 2. Inicializacao do Cliente via `.bat` na Porta `2106`
O jogo deve ser executado atraves do script [Start_Classic.bat](file:///d:/AION%20RUST/AionEMU/AionEMU/Cliente/GFAion/aionclassic/Start_Classic.bat):

| Modo | Comando no `.bat` | Comportamento |
|---|---|---|
| **Sem credenciais** | `start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -classic ...` | Abre a **tela de login in-game** com campos de usuario e senha. O jogador digita suas credenciais normalmente. |
| **Com credenciais** | `start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -account:user -password:pass ...` | O cliente extrai os dados, **pula o formulario** e avanca direto para os Termos de Servico / Lista de Servidores. |

Ambos os metodos funcionam nativamente e sao 100% suportados.

---

## Roadmap do Projeto (Feitos e Pendentes)

Abaixo esta o status detalhado de implementacao de cada modulo do emulador, baseado nas especificacoes cirurgicas do plano de desenvolvimento e validacoes com capturas do servidor oficial:

### Modulos Concluidos e Testados (100% Wire-Accurate)

- [x] **01. [OK] Autenticacao e Handshake do Login-Server**: Protocolo NCSoft porta `2106`, cifra Blowfish com chave dinamica em `0x94`, descriptografia RSA 1024-bit de credenciais, `SM_LOGIN_OK` com flags `0x3F` e `TOS=1`, `SM_SERVER_LIST` com ServerBits `0x401` e CountryCode `2`.
- [x] **02. [OK] Criacao e Selecao de Personagens**: Suporte a todas as racas (Elyos e Asmodians) e 11 classes, persistencia de aparencia em BLOB, validacao de nomes, kits de equipamentos iniciais e skills de nivel 1.
- [x] **03. [OK] Entrada no Mundo e Spawns Oficiais**: Sequencia `SM_ENTER_WORLD_CHECK` (0x1F), spawns reais de Kaisinel Academy e Pandaemonium com **1.054 NPCs oficiais** mapeados com coordenadas e IDs exatos.
- [x] **04. [OK] Movimentacao, Voo, Planagem e Windstreams**: Pacotes `CM_MOVE` (0x14), `SM_PLAYER_MOVE` (0x15), voo de rota `SM_FLY_PATH` (0x31) e estados de corrente de vento `SM_WIND_STATE` (0x2A).
- [x] **05. [OK] Sistema de Combate Fisico/Magico e Auto-Ataque**: Formulas oficiais NCSoft, swing timer de auto-ataque, aggro de monstros, cooldowns de skills e abnormal status `SM_ABNORMAL_STATUS` (0x23).
- [x] **06. [OK] Status, Atributos e Regeneracao**: Pacotes `SM_STATUPDATE_HP` (0x02), `SM_STATUPDATE_MP` (0x04) e `SM_STATUPDATE_DP` (0x06, 2 bytes `u16`), calculo de atributos dinamicos e `SM_EXP_UPDATE` (0x0B).
- [x] **07. [OK] Inventario, Equipamentos e Lojas NPC**: Estrutura `SM_INVENTORY_INFO` (0x17), compra e venda com suporte a recompra (buyback), Kinah e calculo de slots equipados.
- [x] **08. [OK] Dialogos com NPCs e Sistema de Quests**: Janelas interativas `CM_SHOW_DIALOG` (0x34), `CM_DIALOG_SELECT` (0x36), aceitacao, progressao e entrega de missoes com recompensas em `SM_QUEST_LIST` (0x37).
- [x] **09. [OK] Sistema de Legioes/Guildas**: Gerenciamento de legiao, hierarquia de cargos, arvore de buffs (`CM_GUILD_USER_BUY_BUFF` 0xC6) e envio de emblema particionado em **51 chunks**.
- [x] **10. [OK] Sistemas Sociais, Grupos, Aliancas e Amigos**: Convites de Party (`CM_PARTY` 0x60 / `CM_PARTY_BY_NAME` 0x61), lista de amigos com notas (`CM_ADD_BUDDY` 0x6F) e arena de duelos.
- [x] **11. [OK] Sistema de Correio e Mensagens**: Leitura de cartas (`CM_MAIL_READ` 0x87), postman (`CM_MAIL_POSTMAN` 0xA2), 4 variantes de anexo (Kinah, Itens, Express) e persistencia no SQLite.
- [x] **12. [OK] Global Trade Broker**: Registro de anuncios (`CM_GLOBAL_TRADE_REGISTER` 0x0100), historico de vendas (`CM_GLOBAL_TRADE_SALESLOG` 0x0101) e calculo de preco medio.
- [x] **13. [OK] Canais de Chat e Comandos GM**: Canais Normal (50m), Shout (500m), Grupo, Legiao, Sussurros com eco de remetente, anti-flood e comandos administrativos (`.goto`, `.setlevel`, `.teleport`).
- [x] **14. [OK] Banco de Dados SQLite v2 com Migracoes**: Schema relacional completo com modo WAL, integridade referencial e migracoes automaticas entre versoes.
- [x] **15. [OK] Sistema de Teleporte e Portais de Mundo**: Validacao de raca, nivel e custo com `teleport_service`, despacho do pacote oficial `SM_REQUEST_TELEPORT` de 22 bytes e limpeza de cena espacial.

### Modulos em Desenvolvimento e Proximas Etapas

- [ ] **16. [..] IA Avancada de Monstros e Pathfinding GeoEngine**: Integracao de malhas de navegacao (NavMesh), IA comportamental complexa de chefes de raid e habilidades de area.
- [ ] **17. [..] Instancias, Masmorras Privadas e Portais de Raide**: Salas instanciadas com controle de tempo de reentrada (cooldown de instancia) e checkpoints.
- [ ] **18. [..] Coleta, Artesanato e Extracao de Materiais**: Sistema de Crafting (Armorsmithing, Weaponsmithing, Alchemy, Cooking) com chance de critico (Proc).
- [ ] **19. [..] Pets, Minions, Summons de Spiritmaster e Armadilhas**: Controle de comandos de summons (Attack, Stay, Follow), bolsas de pets e deteccao de traps.
- [ ] **20. [..] Housing, Mansoes e Decoracao de Interiores**: Casas em Oriel e Pernon, manutencao semanal e posicionamento de moveis.
- [ ] **21. [..] Batalhas de Fortaleza Abyss (Siege Warfare) e Ranks PvP**: Cronogramas de Fortress Siege, pontuacao Abyss Points (AP), transformacao em Governador/General e reliquias.
- [ ] **22. [..] Daeva Pass, Wardrobe e Atreian Passport**: Interfaces web integradas com recompensas diarias de login e skins de vestuario.

---

## Arquitetura e Mapeamento de Opcodes

### Tabela de Opcodes do Login Server (Porta 2106)

| Opcode | Direcao | Nome do Pacote | Tamanho Wire | Descricao e Estrutura |
|---|---|---|---|---|
| `0x00` | S -> C | `SM_INIT` | 194 bytes | Chave Blowfish em `0x94`, RSA Modulus 128B em `0x09`, Flag `0x03` em `0xA8`, Versao 4.5. |
| `0x0B` | S -> C | `SM_AUTH_GG` | 58 bytes | Payload cifrado GameGuard para liberacao da maquina de estados do cliente. |
| `0x03` | S -> C | `SM_LOGIN_OK` | 78 bytes | Flags de conta `0x3F` (em `0x10..0x20`), assinatura Classic `0xFF 0xFE`, `TOS=1`. |
| `0x04` | S -> C | `SM_SERVER_LIST` | Dinamico | Lista de mundos com ServerBits `0x00000401` (bit 10 Classic) e Bracket `2`. |
| `0x0B` | C -> S | `CM_LOGIN` | 128+ bytes | Pacote de credenciais decifrado via RSA 1024-bit com nome e senha do jogador. |
| `0x02` | C -> S | `CM_PLAY` | 6 bytes | Selecao de mundo; gera token de sessao e responde com `SM_PLAY_OK`. |
| `0x07` | S -> C | `SM_PLAY_OK` | 26 bytes | Chaves de sessao PlayOk1 e PlayOk2 autorizando conexao no Game Server. |

### Tabela de Opcodes do Game Server (Porta 7777)

| Opcode | Direcao | Nome do Pacote | Modulo | Descricao Resumida |
|---|---|---|---|---|
| `0x01` | S -> C | `SM_CHARACTER_LIST` | PLAN-13 | Lista de personagens com raca, classe, nivel, modelo 3D e itens. |
| `0x03` | S -> C | `SM_CREATE_CHARACTER` | PLAN-14 | Criacao de novo personagem e kit de equipamentos. |
| `0x1F` | S -> C | `SM_ENTER_WORLD_CHECK` | PLAN-01 | Handshake de autorizacao de entrada no mapa. |
| `0x18` | S -> C | `SM_PLAYER_SPAWN` | PLAN-01 | Spawna o avatar do jogador em coordenadas de alta precisao. |
| `0x19` | S -> C | `SM_NPC_INFO` | PLAN-01 | Envia templates e posicoes dos 1.054 NPCs do cenario. |
| `0x14` | C -> S | `CM_MOVE` | PLAN-02 | Coordenadas X, Y, Z, Heading e tipo de movimentacao. |
| `0x31` | C -> S | `CM_PATH_FLY` | PLAN-02 | Voo automatico de transporte entre entrepostos. |
| `0x20` | C -> S | `CM_CAST_SPELL` | PLAN-03 | Lancamento de magias e habilidades de classe. |
| `0x1E` | C -> S | `CM_ATTACK` | PLAN-04 | Auto-ataque fisico com swing timer e calculo de dano. |
| `0x02` | S -> C | `SM_STATUPDATE_HP` | PLAN-06 | Atualizacao em tempo real de HP atual e maximo. |
| `0x04` | S -> C | `SM_STATUPDATE_MP` | PLAN-06 | Atualizacao em tempo real de Mana Point (MP). |
| `0x06` | S -> C | `SM_STATUPDATE_DP` | PLAN-06 | Atualizacao em formato oficial de 2 bytes (`u16`) para Divine Points. |
| `0x17` | S -> C | `SM_INVENTORY_INFO` | PLAN-06 | Inventario, slots de equipamentos, manastones e atributos. |
| `0x34` | C -> S | `CM_SHOW_DIALOG` | PLAN-05 | Abertura de dialogos com NPCs (Quests, Lojas, Teleporte). |
| `0x36` | C -> S | `CM_DIALOG_SELECT` | PLAN-05 | Selecao de opcao em dialogo (aceitar/entregar quest ou teleportar). |
| `0x60` | C -> S | `CM_PARTY` | PLAN-10 | Criacao e gerenciamento de grupos de ate 6 jogadores. |
| `0xC6` | C -> S | `CM_GUILD_BUY_BUFF` | PLAN-09 | Aquisicao de buffs de legiao e controle de moedas. |
| `0x87` | C -> S | `CM_MAIL_READ` | PLAN-08 | Leitura e resgate de anexos do correio. |
| `0x0100`| C -> S | `CM_BROKER_REGISTER` | PLAN-11 | Registro de itens para venda no Trade Broker. |
| `0x1B` | C -> S | `CM_CHAT_PUBLIC` | PLAN-12 | Chat geral, shout, grupo, legiao e comandos GM. |
| `0x38` | S -> C | `SM_REQUEST_TELEPORT` | PLAN-15 | Teleporte oficial de 22 bytes com carregamento de mapa. |

---

## Painel Supervisor e Telemetria Day-Trade

O executavel `Auto-Start EmuRust.exe` integra uma interface moderna inspirada em plataformas financeiras profissionais:
* **Grafico Day-Trade Multicurva**:
  * [LS] **Login-Server** (`#38bdf8`)
  * [GS] **Game-Server** (`#10b981`)
  * [CS] **Chat-Server** (`#a855f7`)
  * [LC] **Launcher / Supervisor** (`#eab308`)
  * [TOT] **Consumo Total** (`#ffffff` tracejado)
* **Niveis de Retracao Fibonacci**: Linhas automaticas de referencia (0.0%, 23.6%, 38.2%, 50.0%, 61.8%, 100.0%) para analise visual imediata de picos.
* **Gaveta Lateral (Left Drawer)**: Registradores do sistema (TPS 20.0, Tamanho do DB SQLite, Memoria do SO, Uptime), mapa de portas e link Mobile.
* **Experiencia Mobile iOS-Like**: Dashboard responsivo acessivel via LAN (`http://<LAN-IP>:18080`) com Bottom Tab Bar fosca e Floating Action Button (FAB).

---

## Banco de Dados SQLite Isolado (login.db / game.db / chat.db)

Utiliza bancos de dados SQLite individuais no modo **WAL (Write-Ahead Logging)** com alta concorrencia e schemas integrados das referencias Java 2.4 Classic e Java 4.8 Retail:
* **`login.db`**:
  * `accounts` / `account_data`: Identificadores, nomes, senhas, status de ativacao e niveis de acesso.
  * `account_time`: Tempo acumulado online, sessoes e restricoes.
  * `banned_ip` & `banned_mac`: Controle de bans por endereco IP e MAC.
  * `gameservers`: Registro de mundos e mascaras de conexao.
  * `sessions`: Tokens ativos e chaves de sessao para validacao de transicao Login -> Game.
* **`game.db`**:
  * `characters` / `players`: Personagens, raca, classe, nivel, HP, MP, DP, Kinah, coordenadas e aparencia BLOB.
  * `character_items` / `inventory`: Inventario, slots de equipamento, manastones, godstones e enchant.
  * `character_skills` / `player_skills`: Habilidades aprendidas e niveis.
  * `player_quests`: Missoes ativas, etapas de progresso e missoes concluidas.
  * `character_mail`: Sistema de correio com itens e Kinah anexados (4 variantes).
  * `guilds` / `legions` & `guild_members` / `legion_members`: Legioes, hierarquia e arvore de buffs.
  * `character_buddies`: Lista de amigos e notas.
  * `broker_listings` & `broker_history`: Mercado de negociacao global e historico de transacoes.
  * `abyss_rank`, `player_titles`, `player_effects`, `player_bind_point`.
* **`chat.db`**:
  * `chat_channels` & `chat_bans`: Canais customizados e controle de moderacao.

---

## Comunicacao Inter-Servidores (CS <> LS <> GS)

Assim como na arquitetura dos emuladores Java de referencia, o **EmuRust** opera com portas TCP internas dedicadas e autenticacao obrigatoria por senha configuravel via `launcher.json`:

* **Game-Server -> Login-Server (Porta `9014`)**:
  * Autenticacao com senha (`gameserver_password = "Sabrewolf100!"`).
  * Validada na tabela `gameservers` do banco `login.db`.
  * Sincronizacao de status, heartbeat e contagem de jogadores online em tempo real.
* **Game-Server -> Chat-Server (Porta `9021`)**:
  * Autenticacao com senha (`chat_password = "Sabrewolf100!"`).
  * Sincronizacao e autorizacao de canais de comunicacao.
* **Protecao Ativa**: Conexoes sem a senha correta ou com IDs nao autorizados sao imediatamente recusadas (`REJECTED`) e desconectadas.

---

## Como Iniciar

1. Abra a pasta `Produto Final`.
2. Execute com duplo clique:
   ```text
   Auto-Start EmuRust.exe
   ```
3. No painel, clique em **INICIAR TODOS** (ou use a tecla de atalho).
4. Inicie o jogo pelo script:
   ```text
   Cliente\GFAion\aionclassic\Start_Classic.bat
   ```

---

## Compilacao a partir do Codigo-Fonte

### Pre-requisitos:
* **Rust** (versao 1.80+ x64)
* **Visual Studio 2022 Community** com C++ Build Tools (v143)

### Comandos de Compilacao:

```powershell
# 1. Compilar os Servidores em Rust (Login, Game, Chat, Launcher)
cmd.exe /c "call ""%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && cargo test && cargo build --release"

# 2. Compilar a DLL de Conexao e Telemetria (version.dll x64 e x86)
cmd.exe /c "call ""%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && msbuild Aion-Bin\src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x64 /v:m && msbuild Aion-Bin\src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x86 /v:m"
```
