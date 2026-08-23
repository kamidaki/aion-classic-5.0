# CONTEXT.md — Manual de Engenharia, Protocolos e Arquitetura do EmuRust

> **Documento Mestre de Referência Técnica (100% dos dados de engenharia reversa, protocolos, offsets, opcodes e arquitetura do Aion Classic EU x64).**

---

## 1. Visão Geral da Arquitetura

O **EmuRust** adota a arquitetura de **3 servidores isolados** do emulador Java 4.8 Retail, combinada com uma engine de alta performance em Rust (sem Garbage Collector) e calibrada estritamente para o cliente de 64 bits do **Aion Classic EU (`GFAion\aionclassic\bin64\Aion.bin`)**.

```text

                   AUTO-START EMURUST.EXE (GUI MANAGER)                   
                                                                          
  [ Dashboard Estilo macOS/iOS/Grafana | CPU/RAM | Logs Coloridos | JSON ]

                                     
         
          (Supervisão & Processos)   (Supervisão & Processos)   (Supervisão & Processos)
                                                               
                  
  LOGIN-SERVER               GAME-SERVER               CHAT-SERVER   
                                                                     
 • Auth Protocol  • World / Map    • Channels      
 • STS Protocol     IPC    • NPCs / Spawns    IPC    • Whispers      
 • Named Pipe     (Auth/   • Combat / Sys   (Sync/   • Client Socket 
 • Auto-Accounts  Session) • Entities       Verify)  • Lifecycle     
 • Brute-Force             • Inventory               • Sub-systems   
                  
```

---

## 2. Engenharia Reversa do Client 64-bit (`Aion.bin` & `game.dll`)

| Endereço / Rotina | Instrução / Estrutura Descoberta | Requisito Técnico Obrigatório |
|---|---|---|
| **`0x15A0E0`** | `UI Login Submit Handler` | Exige sessão externa autenticada via Named Pipe ou patch de 6 NOPs (`90 90 90 90 90 90`) no offset `0x15A125`. |
| **`0x842301`** | `movzx ecx, byte ptr [rdx+0xA8]; lea eax, [rcx-0xFD]; cmp al, 1` | O byte no offset `0xA8` do `SM_INIT` **deve ser obrigatoriamente `0xFD`**, seguido pelos 4 bytes da versão 4.5 (`0x04 0x05 0x00 0x00`) para liberar a chave Blowfish. |
| **`0x717BE2`** | `test bl, 0x10` (Account Flags) | As flags da conta no `SM_LOGIN_OK` devem ser `0x0000003F` e o campo TOS (offset `0x30`) deve ser `1`. |
| **`0x717B40`** | `cmp [rbp+67h], 0xFF` e `cmp [rbp+68h], 0xFE` | Assinatura Classic obrigatória: offsets `0x20` e `0x21` do `SM_LOGIN_OK` devem conter `0xFF` e `0xFE`. |
| **`0x84284D`** | `SM_SERVER_LIST Entry (21 Bytes)` | Cada entrada de servidor possui 21 bytes (não 20). O 21º byte é o `CountryCode/Bracket` (valor `2` para Classic EU com `-cc:2`). |
| **`0x842B20`** | `bt r15d, 10; jae 0x842DD8` (ServerBits) | Bit 10 (`0x400`) do campo `ServerBits` deve estar ativo (`0x00000401`) para identificar o servidor como Classic. |
| **`0x843077`** | `Character Counts Parser` | Lê `short(totalServers)` seguido diretamente por 1 byte por servidor com a contagem de personagens criados. |
| **Rejeição Loopback** | Validação interna de IP de destino | O client **descarta `127.0.0.1`** na lista de servidores (`No game server is available (6)`). O anúncio deve ser o IP da LAN (ex: `192.168.3.184`). |
| **Launch Flag** | Linha de comando do client | O client **exige `-loginex`** para ativar a comunicação com o Named Pipe `\\.\pipe\GameforgeClientJSONRPC`. |

---

## 3. Protocolo de Autenticação Gameforge HQ (Porta 13001)

### A. Estrutura de Framing
Texto claro sem cifra:
```text
[u16 length][u8 opcode][3 bytes zero][payload]
```
O tamanho (`u16 length`) inclui os 6 bytes de cabeçalho.

### B. Sequência Completa de Pacotes

#### 1. `0x05 AUTH_GREETING` (Servidor -> Cliente, 92 bytes)
```text
Offset 0x00..0x05: [0x5c, 0x00, 0x05, 0x00, 0x00, 0x00]
Offset 0x06..0x2B: "5B4503FA-8521-4608-BB60-5CFAC87BD63A\0" (UUID Chave 1)
Offset 0x2C..0x51: "7282405F-79E5-49C2-9872-D4F3CC961FF3\0" (UUID Chave 2)
Offset 0x52..0x59: "aiongfc\0" (Nome do serviço)
Offset 0x5A..0x5D: [0x14, 0x0c, 0x00, 0x00] (Trailer)
```

#### 2. `0x01 CREDENTIALS` (Cliente -> Servidor)
Contém o nome de usuário em texto plano terminado em nulo a partir do byte 3: `&payload[3..]`.

#### 3. `0x01 LOGIN_OK` (Servidor -> Cliente, 14 bytes)
```text
Offset 0x00..0x05: [0x0e, 0x00, 0x01, 0x00, 0x00, 0x00]
Offset 0x06..0x09: [u32 LE] AccountId (ex: 0)
Offset 0x0A..0x0D: [u32 LE] LoginKey (ex: 0x026edf39)
```

#### 4. `0x02 SERVER_LIST` (Servidor -> Cliente, 201 bytes)
```text
Offset 0x00..0x05: [0xc9, 0x00, 0x02, 0x00, 0x00, 0x00]
Offset 0x06..0x07: [u16 LE] ServerCount (3)
Offset 0x08..0x46: Entrada 0 (Instância Offline, 63 bytes)
Offset 0x47..0x85: Entrada 1 (Atreia Online, 63 bytes)
Offset 0x86..0xC4: Entrada 2 (Instância Offline, 63 bytes)
Offset 0xC5..0xC8: [0x00, 0x00, 0x00, 0x00] (Trailer)
```

**Estrutura de cada entrada (63 bytes)**:
* `offset 0x00`: `0x01`
* `offset 0x01`: `0x04` (Mundo) ou `0x05` (Instância)
* `offset 0x04`: `0x01` (Online) ou `0x00` (Offline)
* `offset 0x05`: `ServerID` (23 = 0x17 para Atreia)
* `offset 0x09`: `CharacterCount` (quantidade de personagens na conta)
* `offset 0x0D..0x34`: IP em string ASCII terminada em nulo (ex: `"192.168.3.184\0"`)
* `offset 0x35..0x36`: Porta u16 LE (`7777` = `0x1e61`)
* `offset 0x37`: `0x01` (Flag ativo)

#### 5. `0x02 SERVER_SELECT` (Cliente -> Servidor, 10 bytes)
```text
Offset 0x00..0x05: [0x0a, 0x00, 0x02, 0x00, 0x00, 0x00]
Offset 0x06..0x09: [u32 LE] ServerId (0x17 = 23)
```

#### 6. `0x04 SESSION_KEY` (Servidor -> Cliente, 22 bytes)
```text
Offset 0x00..0x05: [0x16, 0x00, 0x04, 0x00, 0x00, 0x00]
Offset 0x06..0x09: [u32 LE] ServerId (0x17)
Offset 0x0A..0x0D: [u32 LE] LoginKey (0x026edf39)
Offset 0x0E..0x11: [u32 LE] ErrorCode (OBRIGATORIAMENTE 0x00000000)
Offset 0x12..0x15: [u32 LE] ExtraFlag (0x00000ad6)
```

---

## 4. Protocolo Federado STS (Porta 6600)

### Framing HTTP/XML
```text
STS/1.0 200 OK\r\n
l:<content_length>\r\n
s:<seq_num>R\r\n
\r\n
<Reply>...</Reply>
```

### Endpoints Implementados
1. `POST /Sts/Connect`: Retorna `<Reply><ServerVersion>1</ServerVersion></Reply>`.
2. `POST /Auth/LoginStart`: Extrai `<LoginName>` da requisição e retorna XML com `UserId`, `LoginName` (`username@local`), `UserName`, `GameAccountId`, `Session` e `LocationId`.
3. `POST /Auth/RequestGameToken`: Emite token temporário e grava na tabela `sessions` do `aion.db`.
4. `POST /Sts/Ping`: Responde `<Reply/>` para manter conexão keepalive.
5. `POST /Auth/LogoutMyClient`: Responde confirmação de desconexão.

---

## 5. Provedor de Named Pipe Windows (`\\.\pipe\GameforgeClientJSONRPC`)

Provedor Win32 nativo que elimina a dependência do `launcher.exe`:
* `ClientLibrary.isClientRunning` -> `true`
* `ClientLibrary.initSession` -> `"dbe9ab65-3818-4e8b-86c5-93a1387a55f2"`
* `ClientLibrary.queryGameDisplayLocale` -> `"en_GB"`
* `ClientLibrary.queryAuthorizationCode` -> `AUTHN_TOKEN` base64 registrado no banco
* `ClientLibrary.queryGameAccountName` -> `username`
* `ClientLibrary.queryGameAccountNumericId` -> `10000001`

---

## 6. Servidor de Mundo (Game-Server, Porta 7777)

*   **Tick Rate**: Fixo em 20 TPS (50ms delta).
*   **Static Data Carregado**:
    *   `39.747` NPCs (`data/client/npcs/client_npcs.xml`)
    *   `76.693` Itens (`data/client/items/client_items.xml`)
    *   `11.476` Skills (`data/client/skills/`)
    *   `1.254` Spawns no mundo (`data/spawns.csv`)
    *   Kits de 8 classes (`data/itens_iniciais.csv`)
*   **Cifra Dinâmica**: Tabela `STATIC_KEY` de 64 bytes (`nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9`) com sub-seed `0x3FF2CC87` e xor-seed `0xCD92E451`.

---

## 7. Servidor Dedicado de Chat (Chat-Server, Porta 10241)

*   **Opcodes de Chat**:
    *   `0x01` (`CM_CHAT_INI` / `SM_CHAT_INI`): Handshake inicial.
    *   `0x02` (`CM_PLAYER_AUTH` / `SM_PLAYER_AUTH_RESPONSE`): Autenticação do jogador.
    *   `0x03` (`CM_CHANNEL_JOIN` / `SM_CHANNEL_RESPONSE`): Inscrição em canais.
    *   `0x04` (`CM_CHANNEL_LEAVE`): Desinscrição de canal.
    *   `0x05` (`CM_CHANNEL_MESSAGE` / `SM_CHANNEL_MESSAGE`): Broadcast de mensagem para os inscritos.
    *   `0x06` (`CM_PING`): Keepalive.
*   **Canais Padrão**: `1: Global_LFG`, `2: Trade`, `3: Region_Sanctum`, `4: Region_Pandaemonium`.

---

## 8. Supervisor & Dashboard (`Auto-Start EmuRust.exe`)

*   **Servidor Web Integrado**: Escuta em `http://127.0.0.1:18080`.
*   **Endpoints de API**:
    *   `GET /api/metrics`: Retorna status, uptime, PID, CPU (%) e RAM (MB) por servidor.
    *   `GET /api/logs?server=all`: Retorna buffer circular dos logs em tempo real.
    *   `POST /api/control/:server/:action`: Permite `start`, `stop`, `restart` individual.
*   **Crash Monitor**: Verifica processos filhos a cada 1.000ms e reinicia automaticamente serviços caídos se `restartOnCrash: true`.
*   **Rotação Física**: Gravação diária em `logs/<servidor>/YYYY-MM-DD.log` com limpeza automática de arquivos com mais de 10 dias.

---

## 9. Esquema do Banco de Dados SQLite (`aion.db`)

```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    access_level INTEGER NOT NULL DEFAULT 0,
    membership INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0,
    last_ip TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    account_id INTEGER NOT NULL DEFAULT 1,
    session_key INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    name TEXT UNIQUE NOT NULL
);
```
