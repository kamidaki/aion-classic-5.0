# CONTEXT.md — Manual de Engenharia, Protocolos e Arquitetura do EmuRust

> **Documento Mestre de Referência Técnica (100% dos dados de engenharia reversa, protocolos, offsets, opcodes e arquitetura do Aion Classic EU x64).**

---

## 1. Regras Obrigatórias e Inegociáveis de Autenticação (Login Rules)

O emulador **EmuRust** segue a mesma filosofia e arquitetura dos emuladores privados consagrados de Aion (Java 4.8 Retail e Java 2.4 Classic Gameforge):

### A. Autenticação Exclusiva por "Login & Senha"
* **Sem dependências externas**: O acesso ao jogo ocorre **exclusivamente com usuário e senha**. Nenhuma autenticação por Launcher proprietário, OAuth, 2FA, SMS ou código de telefone é necessária.
* **Métodos opcionais ignorados**: Todos os fluxos alternativos ou opcionais presentes nos binários do cliente (`Aion.bin` / `game.dll`) são ignorados pelo servidor, exatamente como operam os emuladores de referência.

### B. Modos de Inicialização do Cliente (`Start_Client_Classic_EU.bat`)
O cliente do jogo é inicializado através do arquivo `.bat` apontando para a porta de login padrão `2106`:
```bat
start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu
```

| Modo de Abertura | Comportamento do Cliente | Fluxo no Emulador |
|---|---|---|
| **Sem credenciais no `.bat`** | Abre a **tela de login tradicional in-game** com campos de usuário e senha. | O jogador digita usuário e senha -> O cliente envia `CM_LOGIN` (0x0B/0x12) criptografado com RSA -> Login Server autentica / auto-cria conta no SQLite -> Envia `SM_LOGIN_OK` (0x03) com flags `0x3F` e `TOS=1` -> Abre tela de Seleção de Servidor. |
| **Com credenciais no `.bat`**<br/>(`-account:user -password:pass`) | O cliente extrai os parâmetros, **pula o formulário in-game** e prossegue imediatamente. | Login Server valida as credenciais -> Responde com `SM_LOGIN_OK` -> O cliente abre diretamente na tela de Termos de Serviço / Seleção de Servidores. |

Ambos os modos são 100% suportados e funcionais.

---

## 2. Visão Geral da Arquitetura do Sistema

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AUTO-START EMURUST.EXE (GUI & SUPERVISOR)                    │
│                                                                                 │
│  [ Dashboard Day-Trade Real-Time | Gaveta Lateral | Mobile iOS | Registers ]    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
    (Supervisão de Processo)  (Supervisão de Processo)  (Supervisão de Processo)
                 │                       │                       │
┌────────────────┴──────────────┐ ┌──────┴───────────────┐ ┌─────┴───────────────┐
│         LOGIN-SERVER          │ │        GAME-SERVER   │ │        CHAT-SERVER   │
│  • Auth Protocol NCSoft :2106 │ │  • World / Map Engine│ │  • Channels & LFG    │
│  • Blowfish @ 0x94 & RSA Key  │ │  • NPCs & Spawns     │ │  • Whispers & Flood  │
│  • HQ Protocol :13001         │ │  • Combat & Entities │ │  • Client Sockets    │
│  • STS Protocol :6600         │ │  • 20.0 TPS Locked   │ │  • Porta 10241       │
│  • SQLite aion.db (WAL Mode)  │ │  • Porta 7777        │ │                      │
└───────────────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

---

## 3. Engenharia Reversa do Client 64-bit (`Aion.bin` & `game.dll`)

| Endereço / Rotina | Instrução / Estrutura | Função e Requisito Técnico Obrigatório |
|---|---|---|
| **`0x84222D`** | `movups xmm0, [r8 + rdi + 0x94]` | Chave Blowfish de 16 bytes localizada exatamente no **offset `0x94` (índice 148..164)** do payload `SM_INIT`. |
| **`0x84231B`** | `lea eax, [rcx - 3]; cmp al, 1; ja 0x842353` | O byte no offset `0xA8` (índice `168`) do `SM_INIT` **deve ser `0x03`** para acionar o fluxo de RSA e GameGuard. |
| **`0x842329` / `0x84233E`** | `mov [rbx+0x78], al` (Major/Minor) | Versão 4.5: índices `169` (`0x04`) e `170` (`0x05`) no `SM_INIT`. |
| **`0x842800`** | Jump Table de Opcodes no `game.dll` | `0x00`: `SM_INIT` -> `0x842301`<br>`0x0B`: `SM_AUTH_GG` -> `0x842437` -> `0x149EB0`<br>`0x03`: `SM_LOGIN_OK` -> `0x8424CB`<br>`0x04`: `SM_SERVER_LIST` -> `0x842550` |
| **`0x717BE2`** | `test bl, 0x10` (Account Flags) | As flags da conta no `SM_LOGIN_OK` devem ser `0x0000003F` (em `0x10..0x20`) e o campo TOS (offset `0x30`) deve ser `1`. |
| **`0x717B40`** | `cmp [rbp+67h], 0xFF` e `cmp [rbp+68h], 0xFE` | Assinatura Classic obrigatória: offsets `0x20` e `0x21` do `SM_LOGIN_OK` devem conter `0xFF` e `0xFE`. |
| **`0x84284D`** | `SM_SERVER_LIST Entry (21 Bytes)` | Cada entrada de servidor possui 21 bytes. O 21º byte é o `CountryCode/Bracket` (valor `2` para Classic EU com `-cc:2`). |
| **`0x842B20`** | `bt r15d, 10; jae 0x842DD8` (ServerBits) | Bit 10 (`0x400`) do campo `ServerBits` deve estar ativo (`0x00000401`) para identificar o servidor como Classic. |
| **`0x843077`** | `Character Counts Parser` | Lê `short(totalServers)` seguido diretamente por 1 byte por servidor com a contagem de personagens criados. |

---

## 4. Mapeamento de Protocolos e Opcodes (Wire Oficial)

### A. Login Server — Protocolo NCSoft (Porta 2106)

| Opcode | Direção | Nome do Pacote | Tamanho Wire | Estrutura e Offsets Principais |
|---|---|---|---|---|
| **`0x00`** | S -> C | `SM_INIT` | 194 bytes | `[0x00]` Opcode, `[0x01..0x05]` SessionId, `[0x05..0x09]` Protocol 0xC621, `[0x09..0x89]` RSA Scrambled Modulus (128B), `[0x94..0xA4]` Blowfish Key (16B), `[0xA8]` Flag 0x03, `[0xA9..0xAB]` Version 4.5. |
| **`0x0B`** | S -> C | `SM_AUTH_GG` | 58 bytes | `[0x00]` Opcode, `[0x01..0x05]` SessionId, payload de verificação GameGuard criptografado. |
| **`0x03`** | S -> C | `SM_LOGIN_OK` | 78 bytes | `[0x00]` Opcode, `[0x01..0x05]` AccountId, `[0x05..0x09]` SessionKey1, `[0x10..0x20]` Flags `0x3F` (4x u32), `[0x20..0x22]` Assinatura `0xFF 0xFE`, `[0x30]` TOS=1. |
| **`0x04`** | S -> C | `SM_SERVER_LIST` | Dinâmico | `[0x00]` Opcode, `[0x01]` ServerCount, `[0x02]` LastServer, Entradas de 21B (IP, Porta, Status, ServerBits `0x401`, Bracket `2`), seguido por `u16(totalServers)` e contagens de chars. |
| **`0x0B` / `0x12`** | C -> S | `CM_LOGIN` / `CM_NP_LOGIN` | 128+ bytes | Bloco RSA de 128 bytes contendo credenciais decifradas (`username` e `password`). |
| **`0x02`** | C -> S | `CM_PLAY` | 6 bytes | `[0x00]` Opcode, `[0x01..0x05]` AccountId, `[0x05]` ServerId solicitado. |
| **`0x07`** | S -> C | `SM_PLAY_OK` | 26 bytes | `[0x00]` Opcode, `[0x01..0x05]` PlayOk1, `[0x05..0x09]` PlayOk2, `[0x09]` ServerId. |

### B. Game Server — Protocolo de Jogo (Porta 7777)

| Opcode | Direção | Nome do Pacote | Módulo / PLAN | Estrutura / Campos Principais |
|---|---|---|---|---|
| **`0x01`** | S -> C | `SM_CHARACTER_LIST` | PLAN-13 / PLAN-14 | Lista de personagens, raça, classe, nível, modelo 3D, itens visuais, coordenadas. |
| **`0x03`** | S -> C | `SM_CREATE_CHARACTER` | PLAN-14 | Confirma criação de personagem com kit e atributos iniciais. |
| **`0x05`** | C -> S | `CM_DELETE_CHARACTER` | PLAN-13 | Solicita exclusão com tempo de espera regulamentar. |
| **`0x1F`** | S -> C | `SM_ENTER_WORLD_CHECK` | PLAN-01 | Autoriza carregamento do mapa e entrada do jogador. |
| **`0x18`** | S -> C | `SM_PLAYER_SPAWN` | PLAN-01 | Spawna o jogador em coordenadas exatas de Kaisinel / Pandaemonium. |
| **`0x19`** | S -> C | `SM_NPC_INFO` | PLAN-01 | Envia dados, templates e posições dos 1.054 NPCs oficiais extraídos do wire. |
| **`0x14` / `0x15`** | C -> S / S -> C | `CM_MOVE` / `SM_PLAYER_MOVE` | PLAN-02 | Coordenadas X, Y, Z, Heading, tipo de movimento (correr, andar, pular). |
| **`0x31`** | C -> S / S -> C | `CM_PATH_FLY` / `SM_FLY_PATH` | PLAN-02 | Rota de voo automático de transporte entre postos. |
| **`0x2A` / `0x2B`** | S -> C | `SM_WIND_STATE` / `SM_WIND_PATH_RESULT` | PLAN-02 | Estado de windstream (corrente de vento) e impulso de planagem. |
| **`0x1E` / `0x1D`** | C -> S / S -> C | `CM_ATTACK` / `SM_ATTACK_STATUS` | PLAN-04 | Auto-ataque físico, swing timer, cálculo de dano e resposta de aggro de NPC. |
| **`0x20` / `0x22`** | C -> S / S -> C | `CM_CAST_SPELL` / `SM_SKILL_RESULT` | PLAN-03 | Execução de habilidades físicas/mágicas, custos de MP/DP e cooldowns. |
| **`0x23`** | S -> C | `SM_ABNORMAL_STATUS` | PLAN-03 | Efeitos de buff/debuff com duração e multiplicadores de atributo. |
| **`0x02` / `0x04`** | S -> C | `SM_STATUPDATE_HP` / `SM_STATUPDATE_MP` | PLAN-06 | Atualização instantânea de vida e mana com valores atuais e máximos. |
| **`0x06`** | S -> C | `SM_STATUPDATE_DP` | PLAN-06 | Atualização de Divine Points (DP) em formato de 2 bytes (`u16`). |
| **`0x0B`** | S -> C | `SM_EXP_UPDATE` | PLAN-06 | Atualização de experiência acumulada e necessária para o próximo nível. |
| **`0x17`** | S -> C | `SM_INVENTORY_INFO` | PLAN-06 | Inventário completo, slots equipados, manastones e cálculo de atributos. |
| **`0x33` / `0x35`** | C -> S / S -> C | `CM_BUY_SELL` / `SM_STORE_SALE_INFO` | PLAN-07 | Compra e venda em NPCs com suporte a recompra (buyback) e Kinah. |
| **`0x34` / `0x36`** | C -> S / S -> C | `CM_SHOW_DIALOG` / `CM_DIALOG_SELECT` | PLAN-05 | Janelas de diálogo interativo com NPCs (Missões, Lojas, Teleporte). |
| **`0x37`** | S -> C | `SM_QUEST_LIST` | PLAN-05 | Lista de missões ativas, completadas, etapas e recompensas. |
| **`0x60` / `0x61`** | C -> S / S -> C | `CM_PARTY` / `CM_PARTY_BY_NAME` | PLAN-10 | Sistema de grupos, convites, liderança e distribuição de itens. |
| **`0x6F`** | C -> S / S -> C | `CM_ADD_BUDDY` / `SM_BUDDY_LIST` | PLAN-10 | Lista de amigos, status online/offline e notas personalizadas. |
| **`0xC6` / `0xC7`** | C -> S / S -> C | `CM_GUILD_BUY_BUFF` / `CM_GUILD_MANAGE` | PLAN-09 | Legião/Guilda, membros, árvore de buffs e envio de emblema em 51 chunks. |
| **`0x87` / `0xA2`** | C -> S / S -> C | `CM_MAIL_READ` / `CM_MAIL_POSTMAN` | PLAN-08 | Caixa de correio com 4 variantes de anexo (Kinah, Itens, Express). |
| **`0x0100` / `0x0101`** | C -> S / S -> C | `CM_BROKER_REGISTER` / `CM_BROKER_SALESLOG` | PLAN-11 | Trade Broker Global, registro de anúncios, histórico de vendas e preço médio. |
| **`0x1B` / `0x1C`** | C -> S / S -> C | `CM_CHAT_PUBLIC` / `CM_CHAT_WHISPER` | PLAN-12 | Chat geral, shout, grupo, legião, sussurros privados, anti-flood e comandos GM. |
| **`0x38`** | S -> C | `SM_REQUEST_TELEPORT` | PLAN-15 | Teleporte oficial de 22 bytes (`map_id`, X, Y, Z, Heading) com limpeza de cena. |

---

## 5. Schema do Banco de Dados SQLite v2 (`aion.db`)

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    access_level INTEGER NOT NULL DEFAULT 0,
    membership INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0,
    last_ip TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_id INTEGER NOT NULL DEFAULT 1,
    session_key INTEGER NOT NULL DEFAULT 0,
    issued_at INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0,
    expires_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    name TEXT UNIQUE NOT NULL,
    race INTEGER NOT NULL DEFAULT 0,
    class_id INTEGER NOT NULL DEFAULT 1,
    gender INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    exp INTEGER NOT NULL DEFAULT 0,
    hp INTEGER NOT NULL DEFAULT 1000,
    mp INTEGER NOT NULL DEFAULT 1000,
    dp INTEGER NOT NULL DEFAULT 0,
    title_id INTEGER NOT NULL DEFAULT 0,
    map_id INTEGER NOT NULL DEFAULT 110070000,
    x REAL NOT NULL DEFAULT 457.0,
    y REAL NOT NULL DEFAULT 251.0,
    z REAL NOT NULL DEFAULT 127.04,
    heading INTEGER NOT NULL DEFAULT 0,
    kinah INTEGER NOT NULL DEFAULT 0,
    appearance_data BLOB,
    created_at INTEGER NOT NULL DEFAULT 0,
    last_online INTEGER NOT NULL DEFAULT 0,
    deleted_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS character_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    item_unique_id INTEGER NOT NULL,
    item_template_id INTEGER NOT NULL,
    item_count INTEGER NOT NULL DEFAULT 1,
    item_location INTEGER NOT NULL DEFAULT 0,
    item_slot INTEGER NOT NULL DEFAULT 0,
    enchant_level INTEGER NOT NULL DEFAULT 0,
    fusion_item_id INTEGER NOT NULL DEFAULT 0,
    manastone_count INTEGER NOT NULL DEFAULT 0,
    godstone_id INTEGER NOT NULL DEFAULT 0,
    dye_color INTEGER NOT NULL DEFAULT 0,
    is_equipped INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS character_skills (
    character_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    skill_level INTEGER NOT NULL DEFAULT 1,
    skill_type INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (character_id, skill_id)
);

CREATE TABLE IF NOT EXISTS player_quests (
    player_id INTEGER NOT NULL,
    quest_id INTEGER NOT NULL,
    status INTEGER NOT NULL,
    step INTEGER NOT NULL DEFAULT 0,
    var1 INTEGER NOT NULL DEFAULT 0,
    var2 INTEGER NOT NULL DEFAULT 0,
    var3 INTEGER NOT NULL DEFAULT 0,
    var4 INTEGER NOT NULL DEFAULT 0,
    complete_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, quest_id)
);

CREATE TABLE IF NOT EXISTS character_mail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER NOT NULL,
    sender_name TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    attached_item_id INTEGER NOT NULL DEFAULT 0,
    attached_item_count INTEGER NOT NULL DEFAULT 0,
    attached_kinah INTEGER NOT NULL DEFAULT 0,
    express INTEGER NOT NULL DEFAULT 0,
    is_read INTEGER NOT NULL DEFAULT 0,
    received_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guilds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    leader_id INTEGER NOT NULL,
    contribution_points INTEGER NOT NULL DEFAULT 0,
    coins INTEGER NOT NULL DEFAULT 0,
    emblem_id INTEGER NOT NULL DEFAULT 0,
    buff_tree_level INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    rank INTEGER NOT NULL DEFAULT 0,
    joined_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, player_id)
);

CREATE TABLE IF NOT EXISTS character_buddies (
    character_id INTEGER NOT NULL,
    buddy_id INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (character_id, buddy_id)
);

CREATE TABLE IF NOT EXISTS broker_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    item_unique_id INTEGER NOT NULL,
    item_template_id INTEGER NOT NULL,
    item_count INTEGER NOT NULL,
    price_per_unit INTEGER NOT NULL,
    total_price INTEGER NOT NULL,
    is_sold INTEGER NOT NULL DEFAULT 0,
    is_settled INTEGER NOT NULL DEFAULT 0,
    registered_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS broker_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    item_template_id INTEGER NOT NULL,
    item_count INTEGER NOT NULL,
    price_per_unit INTEGER NOT NULL,
    sold_at INTEGER NOT NULL
);
```

---

## 6. Estrutura de Pastas e Material de Referência (`Docs-Refs/`)

* **`Docs-Refs/Wireshark_Collects_Classic4.5_OficialServer/`**: Capturas binárias reais do tráfego do servidor oficial Gameforge Classic 4.5 (`2026-08-23.pcapng`, `2026-08-23_ultimacoleta.pcapng`, `ROTEIRO-CONTA-NOVA.txt`, `Some informations about packets.txt`).
* **`Docs-Refs/PLAN_DEVELOPMENT_FUNCTIONS/`**: 16 especificações cirúrgicas baseadas em wire capture oficial (PLAN-00 a PLAN-15, 100% implementados).
* **`Docs-Refs/PLANO-DESENVOLVIMENTO/`**: 22 documentos de visão arquitetural, subsistemas e engenharia reversa de pacotes.
* **`Docs-Refs/PLANO-LOGINSERVER/`**: 20 documentos de auditoria, análise dos protocolos STS/NCSoft/HQ e arquitetura do login server.
* **`Docs-Refs/JAVA EMU - 2.4 CLASSIC EU/`**: Base de referência Java para pacotes de versão Classic EU 2.4.
* **`Docs-Refs/JAVA EMU - 4.8 RETAIL/`**: Base de referência Java para sistemas 4.x Retail (geodata, templates XML, packet handlers).
* **`Docs-Refs/reference/`**: Repositório Aion-Lightning, ferramentas PacketSamurai e POC .NET.
* **`Docs-Refs/Backup Oriiginal do Version.dll (No-IP)/`**: Backup e código fonte original da DLL de conexão No-IP.

---

## 7. Changelog de Correções e Evoluções do Sistema

### 16. Correção Definitiva do Fluxo de Login In-Game e Isolamento dos Bancos de Dados
* **Problema Identificado**: 
  - Ao conectar na porta 2106, o servidor executava uma cadeia proativa prematura que auto-criava uma conta estática `"teste"` com permissões elevadas e enviava `SM_AUTH_GG`, `SM_LOGIN_OK` e `SM_SERVER_LIST` antes do jogador digitar suas credenciais no formulário in-game.
  - Isso dessincronizava a máquina de estados do cliente, fazendo o botão "OK" travar/congelar ao digitar `fly` / `fly`.
* **Como foi corrigido**:
  1. **Remoção da cadeia proativa prematura**: O servidor envia exclusivamente o `SM_INIT` (Opcode 0x00 com chave Blowfish em `0x94` e RSA Scrambled Modulus) na conexão TCP e entra em escuta reativa assíncrona.
  2. **Processamento Real de Credenciais RSA**: O pacote `CM_LOGIN` / `CM_NP_LOGIN` (Opcode `0x0B` / `0x12`) enviado pelo cliente ao clicar em "OK" tem seu bloco RSA de 128 bytes decifrado pela chave privada do servidor, obtendo exatamente o usuário e senha digitados in-game (ex: `fly` / `fly`).
  3. **Auto-criação Limpa no Banco**: Cria a conta real no banco de dados com `access_level: 0, membership: 0`, e envia `SM_LOGIN_OK` (0x03, 78 bytes, flags `0x3F`, assinatura `0xFF 0xFE`, `TOS=1`) seguido imediatamente por `SM_SERVER_LIST` (0x04) com a contagem real de personagens.
  4. **Isolamento de Bancos de Dados SQLite por Servidor**:
     - `login.db`: Tabelas `accounts`, `account_data`, `account_time`, `banned_ip`, `banned_mac`, `gameservers`, `sessions`.
     - `game.db`: Tabelas `characters`, `players`, `character_items`, `inventory`, `character_skills`, `player_skills`, `player_quests`, `character_mail`, `guilds`, `guild_members`, `legions`, `legion_members`, `character_buddies`, `broker_listings`, `broker_history`, `abyss_rank`, `player_titles`, `player_effects`, `player_bind_point`.
     - `chat.db`: Tabelas `chat_channels`, `chat_bans`.
     - Consulta cruzada transparente de sessões via `ATTACH DATABASE 'login.db' AS login_db`.
  5. **100% dos 176 testes automatizados aprovados e compatibilidade total validada**.

---

## 8. Arquitetura de Comunicação Inter-Servidores (CS <> LS <> GS)

O emulador **EmuRust** implementa a mesma arquitetura de segurança de rede inter-servidores do **Java AionEMU (Aion-Lightning / Encom 2.4 Classic)**, utilizando portas TCP internas dedicadas com autenticação obrigatória por senha criptografada:

### A. Tabela de Portas e Credenciais Inter-Servidores

| Conexão | Porta Interna | Papel do Servidor | Senha Padrão (`launcher.json`) | Validação no DB |
|---|---|---|---|---|
| **GS -> LS** | `TCP 9014` | **Login Server** escuta conexões internas do Game Server. | `"Sabrewolf100!"` | Tabela `gameservers` (`login.db`) e chave `gameserver_password`. |
| **GS -> CS** | `TCP 9021` | **Chat Server** escuta conexões internas do Game Server. | `"Sabrewolf100!"` | Chave `chat_password` no `launcher.json`. |

### B. Protocolo de Handshake e Registro

```text
┌──────────────┐                               ┌──────────────┐
│ Game-Server  │                               │ Login-Server │
└──────┬───────┘                               └──────┬───────┘
       │                                              │
       │  CM_GS_AUTH (server_id, port, max, pass)     │
       │─────────────────────────────────────────────>│ (Valida senha no gameservers e launcher.json)
       │                                              │
       │  SM_GS_AUTH_RESPONSE (Status 0 = AUTHED)     │
       │<─────────────────────────────────────────────│ (Registra GameServer no Active Registry)
       │                                              │
       │  CM_GS_PONG / Heartbeat (a cada 15s)         │
       │<────────────────────────────────────────────>│
       │                                              │
```

1. **Rejeição Automática**: Se um Game Server ou Chat Server tentar se conectar com senha incorreta ou ID não registrado, a conexão é **imediatamente rejeitada com código 1 (`REJECTED`)** e o socket é encerrado.
2. **Sincronização em Tempo Real**: O Login Server atualiza dinamicamente a contagem de jogadores online no `SM_SERVER_LIST` conforme o Game Server envia os relatórios periódicos de status.
3. **Resiliência e Reconexão Automática**: O Game Server monitora a saúde das conexões com o Login Server e Chat Server, efetuando reconexão automática em caso de reinício de qualquer serviço.

---

## 9. Parâmetros de Configuração Avançados (Mapeamento Java `network.properties` & `gameserver.properties`)

O emulador unifica todas as propriedades dos arquivos Java em um único arquivo de configuração JSON centralizado ([launcher.json](file:///d:/AION%20RUST/AionEMU/AionEMU/Produto%20Final/config/launcher.json)):

### A. Mapeamento `network.properties`

| Parâmetro Java (`network.properties`) | Equivalente `launcher.json` | Padrão | Descrição |
|---|---|---|---|
| `gameserver.network.client.port` | `port` | `7777` | Porta TCP do Game Server para conexão dos clientes. |
| `gameserver.network.client.host` | `bind_address` | `"127.0.0.1"` | Interface de escuta TCP (`0.0.0.0` para WAN ou `127.0.0.1` para local). |
| `gameserver.network.client.maxplayers` | `max_players` | `1000` | Limite máximo de jogadores conectados simultaneamente. |
| `gameserver.network.login.address` | `login_server_address` | `"127.0.0.1:9014"` | Endereço interno do Login Server. |
| `gameserver.network.login.gsid` | `server_id` | `1` | ID único de registro deste Game Server no Login Server. |
| `gameserver.network.login.password` | `gameserver_password` | `"Sabrewolf100!"` | Senha de autenticação do Game Server no Login Server. |
| `gameserver.network.chat.address` | `chat_server_address` | `"127.0.0.1:9021"` | Endereço interno do Chat Server. |
| `gameserver.network.chat.password` | `chat_password` | `"Sabrewolf100!"` | Senha de autenticação no Chat Server. |
| `gameserver.network.nio.threads` | `nio_threads` | `4` | Quantidade de threads assíncronas dedicadas para I/O de rede. |
| `gameserver.network.packet.processor.threads.min` | `processor_threads_min` | `4` | Threads mínimas no pool de processamento de pacotes do cliente. |
| `gameserver.network.packet.processor.threads.max` | `processor_threads_max` | `16` | Threads máximas no pool de processamento de pacotes. |
| `gameserver.network.packet.processor.threshold.kill` | `processor_threshold_kill` | `3` | Limiar de inatividade para redução do pool de processamento. |
| `gameserver.network.packet.processor.threshold.spawn` | `processor_threshold_spawn` | `50` | Limiar de pacotes enfileirados para criação de nova thread de processamento. |
| `gameserver.network.display.unknownpackets` | `display_unknown_packets` | `false` | Exibe ou oculta logs de pacotes e opcodes não tratados. |
| `gameserver.network.display.packets` | `display_packets` | `false` | Exibe ou oculta dumps detalhados de cada pacote processado. |
| `gameserver.network.flood.*` | `flood_protection` | `enabled: false` | Proteção contra flood e spam de conexões TCP. |

### B. Mapeamento `gameserver.properties`

| Parâmetro Java (`gameserver.properties`) | Equivalente `launcher.json` | Padrão | Descrição |
|---|---|---|---|
| `gameserver.country.code` | `gameplay.country_code` | `2` | Código de país da região (0: KR, 1: NA, 2: EU Classic, 7: RUS). |
| `gameserver.chatserver.enable` | `gameplay.chat_server_enable` | `true` | Habilita a sincronização com o Chat Server. |
| `gameserver.character.limit.count` | `gameplay.character_limit_count` | `8` | Quantidade máxima de personagens permitidos por conta. |
| `gameserver.character.creation.mode` | `gameplay.character_creation_mode` | `1` | Modo de facção (0: única facção por conta, 1: Elyos e Asmodians permitidos). |
| `gameserver.players.max.level` | `gameplay.players_max_level` | `55` | Nível máximo permitido para os personagens. |
| `gameserver.starting.level` | `gameplay.starting_level` | `1` | Nível inicial de novos personagens criados. |
| `gameserver.startClass.maxLevel` | `gameplay.start_class_max_level` | `10` | Nível máximo da classe inicial antes da ascensão para Daeva. |
| `gameserver.name` | `server_name` | `"Brasil em Chamas"` | Nome oficial de exibição do servidor no lobby. |
| `gameserver.name.characterpattern` | `gameplay.character_name_pattern` | `"^[a-zA-Z0-9]{2,16}$"` | Expressão regular (Regex) para validação do nome do personagem. |
| `gameserver.character.reentry.time` | `gameplay.character_reentry_time_secs` | `20` | Tempo de espera (cooldown em segundos) para troca de personagem. |

> [!NOTE]
> **Zero Garbage Collection (Zero GC)**: Propriedades de Garbage Collection do Java (`gc_enable`, `gc_optimization_mins`) são desnecessárias e foram eliminadas no Rust, uma vez que o emulador utiliza gerenciamento determinístico de memória nativo via RAII, lifetimes e drop semantics, garantindo 0ms de pausas e consumo estável de memória.
