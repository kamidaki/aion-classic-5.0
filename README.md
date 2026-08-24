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

## Índice

1. [Visão Geral](#visão-geral)
2. [Regras Obrigatórias de Autenticação e Login](#regras-obrigatórias-de-autenticação-e-login)
3. [Roadmap do Projeto (Feitos e Pendentes)](#roadmap-do-projeto-feitos-e-pendentes)
4. [Arquitetura e Mapeamento de Opcodes](#arquitetura-e-mapeamento-de-opcodes)
5. [Painel Supervisor & Telemetria Day-Trade](#painel-supervisor--telemetria-day-trade)
6. [Login Server & Criptografia](#1-login-server)
7. [Game Server & Mundo](#2-game-server)
8. [Chat Server & Redes](#3-chat-server)
9. [Banco de Dados SQLite v2](#banco-de-dados-sqlite-v2)
10. [Como Iniciar o Emulador](#como-iniciar)
11. [Compilação a partir do Código-Fonte](#compilação-a-partir-do-código-fonte)

---

## Visão Geral

O **EmuRust** é uma reimplementação nativa, em **Rust**, do ecossistema de servidor necessário para operar o cliente **Aion Classic EU (Gameforge)** em sua versão 4.5. Diferente dos emuladores tradicionais em Java, esta stack foi construída para entregar **zero microtravamentos (Zero Garbage Collection)**, consumo ocioso de 0.00% de CPU, tick rate cravado em 20.0 TPS e fidelidade absoluta byte a byte com as capturas oficiais de rede do Wireshark.

---

## Regras Obrigatórias de Autenticação e Login

Seguindo o padrão consolidado dos emuladores privados consagrados de Aion (Java 4.8 Retail e Java 2.4 Classic Gameforge):

### 1. Autenticação Pura por "Login & Senha"
* **Sem dependências externas**: O login acontece **exclusivamente com usuário e senha**. Nenhuma autenticação por Launcher externo, OAuth, 2FA, SMS ou código de telefone é necessária.
* **Métodos opcionais desconsiderados**: Todos os métodos alternativos presentes nos binários do cliente são ignorados pelo emulador, mantendo o processo limpo, direto e compatível.

### 2. Inicialização do Cliente via `.bat` na Porta `2106`
O jogo deve ser executado através do script [Start_Client_Classic_EU.bat](file:///d:/AION%20RUST/AionEMU/AionEMU/Cliente/GFAion/aionclassic/Start_Client_Classic_EU.bat):

| Modo | Comando no `.bat` | Comportamento |
|---|---|---|
| **Sem credenciais** | `start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -classic ...` | Abre a **tela de login in-game** com campos de usuário e senha. O jogador digita suas credenciais normalmente. |
| **Com credenciais** | `start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -account:user -password:pass ...` | O cliente extrai os dados, **pula o formulário** e avança direto para os Termos de Serviço / Lista de Servidores. |

Ambos os métodos funcionam nativamente e são 100% suportados.

---

## Roadmap do Projeto (Feitos e Pendentes)

Abaixo está o status detalhado de implementação de cada módulo do emulador, baseado nas especificações cirúrgicas do plano de desenvolvimento e validações com capturas do servidor oficial:

### 🟢 Módulos Concluídos e Testados (100% Wire-Accurate)

- [x] **01. 🛡️ Autenticação e Handshake do Login-Server**: Protocolo NCSoft porta `2106`, cifra Blowfish com chave dinâmica em `0x94`, descriptografia RSA 1024-bit de credenciais, `SM_LOGIN_OK` com flags `0x3F` e `TOS=1`, `SM_SERVER_LIST` com ServerBits `0x401` e CountryCode `2`.
- [x] **02. 👥 Criação e Seleção de Personagens**: Suporte a todas as raças (Elyos e Asmodians) e 11 classes, persistência de aparência em BLOB, validação de nomes, kits de equipamentos iniciais e skills de nível 1.
- [x] **03. 🌍 Entrada no Mundo e Spawns Oficiais**: Sequência `SM_ENTER_WORLD_CHECK` (0x1F), spawns reais de Kaisinel Academy e Pandaemonium com **1.054 NPCs oficiais** mapeados com coordenadas e IDs exatos.
- [x] **04. 🕊️ Movimentação, Voo, Planagem e Windstreams**: Pacotes `CM_MOVE` (0x14), `SM_PLAYER_MOVE` (0x15), voo de rota `SM_FLY_PATH` (0x31) e estados de corrente de vento `SM_WIND_STATE` (0x2A).
- [x] **05. ⚔️ Sistema de Combate Físico/Mágico e Auto-Ataque**: Fórmulas oficiais NCSoft, swing timer de auto-ataque, aggro de monstros, cooldowns de skills e abnormal status `SM_ABNORMAL_STATUS` (0x23).
- [x] **06. 📊 Status, Atributos e Regeneração**: Pacotes `SM_STATUPDATE_HP` (0x02), `SM_STATUPDATE_MP` (0x04) e `SM_STATUPDATE_DP` (0x06, 2 bytes `u16`), cálculo de atributos dinâmicos e `SM_EXP_UPDATE` (0x0B).
- [x] **07. 🎒 Inventário, Equipamentos e Lojas NPC**: Estrutura `SM_INVENTORY_INFO` (0x17), compra e venda com suporte a recompra (buyback), Kinah e cálculo de slots equipados.
- [x] **08. 📜 Diálogos com NPCs e Sistema de Quests**: Janelas interativas `CM_SHOW_DIALOG` (0x34), `CM_DIALOG_SELECT` (0x36), aceitação, progressão e entrega de missões com recompensas em `SM_QUEST_LIST` (0x37).
- [x] **09. 🏰 Sistema de Legiões/Guildas**: Gerenciamento de legião, hierarquia de cargos, árvore de buffs (`CM_GUILD_USER_BUY_BUFF` 0xC6) e envio de emblema particionado em **51 chunks**.
- [x] **10. 🤝 Sistemas Sociais, Grupos, Alianças e Amigos**: Convites de Party (`CM_PARTY` 0x60 / `CM_PARTY_BY_NAME` 0x61), lista de amigos com notas (`CM_ADD_BUDDY` 0x6F) e arena de duelos.
- [x] **11. 📬 Sistema de Correio e Mensagens**: Leitura de cartas (`CM_MAIL_READ` 0x87), postman (`CM_MAIL_POSTMAN` 0xA2), 4 variantes de anexo (Kinah, Itens, Express) e persistência no SQLite.
- [x] **12. 📈 Global Trade Broker**: Registro de anúncios (`CM_GLOBAL_TRADE_REGISTER` 0x0100), histórico de vendas (`CM_GLOBAL_TRADE_SALESLOG` 0x0101) e cálculo de preço médio.
- [x] **13. 💬 Canais de Chat e Comandos GM**: Canais Normal (50m), Shout (500m), Grupo, Legião, Sussurros com eco de remetente, anti-flood e comandos administrativos (`.goto`, `.setlevel`, `.teleport`).
- [x] **14. 💾 Banco de Dados SQLite v2 com Migrações**: Schema relacional completo com modo WAL, integridade referencial e migrações automáticas entre versões.
- [x] **15. 🌀 Sistema de Teleporte e Portais de Mundo**: Validação de raça, nível e custo com `teleport_service`, despacho do pacote oficial `SM_REQUEST_TELEPORT` de 22 bytes e limpeza de cena espacial.

### 🟡 Módulos em Desenvolvimento e Próximas Etapas

- [ ] **16. 🧠 IA Avançada de Monstros e Pathfinding GeoEngine**: Integração de malhas de navegação (NavMesh), IA comportamental complexa de chefes de raid e habilidades de área.
- [ ] **17. 🏰 Instâncias, Masmorras Privadas e Portais de Raide**: Salas instanciadas com controle de tempo de reentrada (cooldown de instância) e checkpoints.
- [ ] **18. ⚒️ Coleta, Artesanato e Extração de Materiais**: Sistema de Crafting (Armorsmithing, Weaponsmithing, Alchemy, Cooking) com chance de crítico (Proc).
- [ ] **19. 🐾 Pets, Minions, Summons de Spiritmaster e Armadilhas**: Controle de comandos de summons (Attack, Stay, Follow), bolsas de pets e detecção de traps.
- [ ] **20. 🏡 Housing, Mansões e Decoração de Interiores**: Casas em Oriel e Pernon, manutenção semanal e posicionamento de móveis.
- [ ] **21. ⚔️ Batalhas de Fortaleza Abyss (Siege Warfare) e Ranks PvP**: Cronogramas de Fortress Siege, pontuação Abyss Points (AP), transformação em Governador/General e relíquias.
- [ ] **22. 🎁 Daeva Pass, Wardrobe e Atreian Passport**: Interfaces web integradas com recompensas diárias de login e skins de vestuário.

---

## Arquitetura e Mapeamento de Opcodes

### Tabela de Opcodes do Login Server (Porta 2106)

| Opcode | Direção | Nome do Pacote | Tamanho Wire | Descrição e Estrutura |
|---|---|---|---|---|
| `0x00` | S ➔ C | `SM_INIT` | 194 bytes | Chave Blowfish em `0x94`, RSA Modulus 128B em `0x09`, Flag `0x03` em `0xA8`, Versão 4.5. |
| `0x0B` | S ➔ C | `SM_AUTH_GG` | 58 bytes | Payload cifrado GameGuard para liberação da máquina de estados do cliente. |
| `0x03` | S ➔ C | `SM_LOGIN_OK` | 78 bytes | Flags de conta `0x3F` (em `0x10..0x20`), assinatura Classic `0xFF 0xFE`, `TOS=1`. |
| `0x04` | S ➔ C | `SM_SERVER_LIST` | Dinâmico | Lista de mundos com ServerBits `0x00000401` (bit 10 Classic) e Bracket `2`. |
| `0x0B` | C ➔ S | `CM_LOGIN` | 128+ bytes | Pacote de credenciais decifrado via RSA 1024-bit com nome e senha do jogador. |
| `0x02` | C ➔ S | `CM_PLAY` | 6 bytes | Seleção de mundo; gera token de sessão e responde com `SM_PLAY_OK`. |
| `0x07` | S ➔ C | `SM_PLAY_OK` | 26 bytes | Chaves de sessão PlayOk1 e PlayOk2 autorizando conexão no Game Server. |

### Tabela de Opcodes do Game Server (Porta 7777)

| Opcode | Direção | Nome do Pacote | Módulo | Descrição Resumida |
|---|---|---|---|---|
| `0x01` | S ➔ C | `SM_CHARACTER_LIST` | PLAN-13 | Lista de personagens com raça, classe, nível, modelo 3D e itens. |
| `0x03` | S ➔ C | `SM_CREATE_CHARACTER` | PLAN-14 | Criação de novo personagem e kit de equipamentos. |
| `0x1F` | S ➔ C | `SM_ENTER_WORLD_CHECK` | PLAN-01 | Handshake de autorização de entrada no mapa. |
| `0x18` | S ➔ C | `SM_PLAYER_SPAWN` | PLAN-01 | Spawna o avatar do jogador em coordenadas de alta precisão. |
| `0x19` | S ➔ C | `SM_NPC_INFO` | PLAN-01 | Envia templates e posições dos 1.054 NPCs do cenário. |
| `0x14` | C ➔ S | `CM_MOVE` | PLAN-02 | Coordenadas X, Y, Z, Heading e tipo de movimentação. |
| `0x31` | C ➔ S | `CM_PATH_FLY` | PLAN-02 | Voo automático de transporte entre entrepostos. |
| `0x20` | C ➔ S | `CM_CAST_SPELL` | PLAN-03 | Lançamento de magias e habilidades de classe. |
| `0x1E` | C ➔ S | `CM_ATTACK` | PLAN-04 | Auto-ataque físico com swing timer e cálculo de dano. |
| `0x02` | S ➔ C | `SM_STATUPDATE_HP` | PLAN-06 | Atualização em tempo real de HP atual e máximo. |
| `0x04` | S ➔ C | `SM_STATUPDATE_MP` | PLAN-06 | Atualização em tempo real de Mana Point (MP). |
| `0x06` | S ➔ C | `SM_STATUPDATE_DP` | PLAN-06 | Atualização em formato oficial de 2 bytes (`u16`) para Divine Points. |
| `0x17` | S ➔ C | `SM_INVENTORY_INFO` | PLAN-06 | Inventário, slots de equipamentos, manastones e atributos. |
| `0x34` | C ➔ S | `CM_SHOW_DIALOG` | PLAN-05 | Abertura de diálogos com NPCs (Quests, Lojas, Teleporte). |
| `0x36` | C ➔ S | `CM_DIALOG_SELECT` | PLAN-05 | Seleção de opção em diálogo (aceitar/entregar quest ou teleportar). |
| `0x60` | C ➔ S | `CM_PARTY` | PLAN-10 | Criação e gerenciamento de grupos de até 6 jogadores. |
| `0xC6` | C ➔ S | `CM_GUILD_BUY_BUFF` | PLAN-09 | Aquisição de buffs de legião e controle de moedas. |
| `0x87` | C ➔ S | `CM_MAIL_READ` | PLAN-08 | Leitura e resgate de anexos do correio. |
| `0x0100`| C ➔ S | `CM_BROKER_REGISTER` | PLAN-11 | Registro de itens para venda no Trade Broker. |
| `0x1B` | C ➔ S | `CM_CHAT_PUBLIC` | PLAN-12 | Chat geral, shout, grupo, legião e comandos GM. |
| `0x38` | S ➔ C | `SM_REQUEST_TELEPORT` | PLAN-15 | Teleporte oficial de 22 bytes com carregamento de mapa. |

---

## Painel Supervisor & Telemetria Day-Trade

O executável `Auto-Start EmuRust.exe` integra uma interface moderna inspirada em plataformas financeiras profissionais:
* **Gráfico Day-Trade Multicurva**:
  * 🔵 **Login-Server** (`#38bdf8`)
  * 🟢 **Game-Server** (`#10b981`)
  * 🟣 **Chat-Server** (`#a855f7`)
  * 🟡 **Launcher / Supervisor** (`#eab308`)
  * ⚪ **Consumo Total** (`#ffffff` tracejado)
* **Níveis de Retração Fibonacci**: Linhas automáticas de referência (0.0%, 23.6%, 38.2%, 50.0%, 61.8%, 100.0%) para análise visual imediata de picos.
* **Gaveta Lateral (Left Drawer)**: Registradores do sistema (TPS 20.0, Tamanho do DB SQLite, Memória do SO, Uptime), mapa de portas e link Mobile.
* **Experiência Mobile iOS-Like**: Dashboard responsivo acessível via LAN (`http://<LAN-IP>:18080`) com Bottom Tab Bar fosca e Floating Action Button (FAB).

---

## Banco de Dados SQLite v2

Utiliza **SQLite** no modo **WAL (Write-Ahead Logging)** de altíssima concorrência:
* `accounts`: Identificadores, nomes, senhas e níveis de acesso (GM).
* `sessions`: Tokens ativos para validação de transição Login ➔ Game.
* `characters`: Personagens criados, raça, classe, nível, HP, MP, DP, Kinah e coordenadas.
* `character_items`: Inventário, slots de equipamento, manastones e enchant.
* `character_skills`: Habilidades aprendidas e níveis.
* `player_quests`: Missões ativas, etapas e missões concluídas.
* `character_mail`: Sistema de correio com itens e Kinah anexados.
* `guilds` & `guild_members`: Legiões, hierarquia e árvore de buffs.
* `character_buddies`: Lista de amigos e notas.
* `broker_listings` & `broker_history`: Mercado de negociação global.

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
   Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
   ```

---

## Compilação a partir do Código-Fonte

### Pré-requisitos:
* **Rust** (versão 1.80+ x64)
* **Visual Studio 2022 Community** com C++ Build Tools (v143)

### Comandos de Compilação:

```powershell
# 1. Compilar os Servidores em Rust (Login, Game, Chat, Launcher)
cmd.exe /c "call ""%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && cargo test && cargo build --release"

# 2. Compilar a DLL de Conexão e Telemetria (version.dll x64 e x86)
cmd.exe /c "call ""%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && msbuild Aion-Bin\src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x64 /v:m && msbuild Aion-Bin\src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x86 /v:m"
```
