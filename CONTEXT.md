# CONTEXT.md — Manual de Engenharia, Protocolos e Arquitetura do EmuRust

> **Documento Mestre de Referência Técnica (100% dos dados de engenharia reversa, protocolos, offsets, opcodes e arquitetura do Aion Classic EU x64).**

---

## 1. Visão Geral da Arquitetura

O **EmuRust** adota a arquitetura de **3 servidores isolados** do emulador Java 4.8 Retail, combinada com uma engine de alta performance em Rust (sem Garbage Collector) e calibrada estritamente para o cliente de 64 bits do **Aion Classic EU (`GFAion\aionclassic\bin64\Aion.bin`)**.

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
│  • Auth Protocol NCSoft / GF  │ │  • World / Map Engine│ │  • Channels & LFG    │
│  • Blowfish @ 0x94 & RSA Key  │ │  • NPCs / Spawns     │ │  • Whispers          │
│  • STS & Named Pipe           │ │  • Combat & Entities │ │  • Client Sockets    │
│  • SQLite aion.db (WAL Mode)  │ │  • 20.0 TPS Locked   │ │  • Port 10241        │
│  • Portas 2106 / 6600 / 13001 │ │  • Porta 7777        │ │                      │
└───────────────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

---

## 2. Engenharia Reversa do Client 64-bit (`Aion.bin` & `game.dll`)

| Endereço / Rotina | Instrução / Estrutura Descoberta | Requisito Técnico Obrigatório |
|---|---|---|
| **`0x84222D`** | `movups xmm0, [r8 + rdi + 0x94]` | Chave Blowfish de 16 bytes localizada exatamente no **offset `0x94` (índice 148..164)** do payload `SM_INIT`. |
| **`0x84231B`** | `lea eax, [rcx - 3]; cmp al, 1; ja 0x842353` | O byte no offset `0xA8` (índice `168`) do `SM_INIT` **deve ser `0x03`** para acionar o fluxo de RSA e GameGuard. |
| **`0x842329` / `0x84233E`** | `mov [rbx+0x78], al` (Major/Minor) | Versão 4.5: índices `169` (`0x04`) e `170` (`0x05`) no `SM_INIT`. |
| **`0x842800`** | Jump Table de Opcodes no `game.dll` | `0x00`: `SM_INIT` -> `0x842301`<br>`0x0B`: `SM_AUTH_GG` -> `0x842437` -> `0x149EB0`<br>`0x03`: `SM_LOGIN_OK` -> `0x8424CB`<br>`0x04`: `SM_SERVER_LIST` -> `0x842550` |
| **`0x15A125`** | `UI Login Button JNE` | Desvio condicional do botão de login. NOPpado pelo `version.dll` para garantir submissão contínua. |
| **`0x843E42` / `0x843E4B`** | `Socket Guard JEs` | Guardas de envio de pacotes NOPpadas pelo `version.dll` para garantir despacho TCP sem descartes. |
| **`0x717BE2`** | `test bl, 0x10` (Account Flags) | As flags da conta no `SM_LOGIN_OK` devem ser `0x0000003F` e o campo TOS (offset `0x30`) deve ser `1`. |
| **`0x717B40`** | `cmp [rbp+67h], 0xFF` e `cmp [rbp+68h], 0xFE` | Assinatura Classic obrigatória: offsets `0x20` e `0x21` do `SM_LOGIN_OK` devem conter `0xFF` e `0xFE`. |
| **`0x84284D`** | `SM_SERVER_LIST Entry (21 Bytes)` | Cada entrada de servidor possui 21 bytes. O 21º byte é o `CountryCode/Bracket` (valor `2` para Classic EU com `-cc:2`). |
| **`0x842B20`** | `bt r15d, 10; jae 0x842DD8` (ServerBits) | Bit 10 (`0x400`) do campo `ServerBits` deve estar ativo (`0x00000401`) para identificar o servidor como Classic. |
| **`0x843077`** | `Character Counts Parser` | Lê `short(totalServers)` seguido diretamente por 1 byte por servidor com a contagem de personagens criados. |

---

## 3. Protocolo de Autenticação Gameforge HQ (Porta 13001)

### A. Estrutura de Framing
```text
[u16 length][u8 opcode][3 bytes zero][payload]
```
O tamanho (`u16 length`) inclui os 6 bytes de cabeçalho.

### B. Sequência de Pacotes
1. **`0x05 AUTH_GREETING`** (Servidor -> Cliente, 92 bytes)
2. **`0x01 CREDENTIALS`** (Cliente -> Servidor, payload com nome da conta)
3. **`0x01 LOGIN_OK`** (Servidor -> Cliente, 14 bytes)
4. **`0x02 SERVER_LIST`** (Servidor -> Cliente, 201 bytes)
5. **`0x02 SERVER_SELECT`** (Cliente -> Servidor, 10 bytes)
6. **`0x06 PLAY_OK`** (Servidor -> Cliente, 14 bytes)

---

## 4. Protocolo NCSoft Nativo (Porta 2106)

### A. Cifra Blowfish
* Algoritmo Blowfish com blocos de 64 bits (8 bytes).
* Seed de chave dinâmica enviada no `SM_INIT` no offset `0x94` (índice 148..164).
* Chave inicial padrão: `[0x6b, 0x60, 0xcb, 0x5b, 0x82, 0xce, 0x90, 0xb1, 0xcc, 0x2b, 0x6c, 0x55, 0x6c, 0x6c, 0x6c, 0x6c]`.
* Checksum cumulativo de 32 bits no trailer de cada pacote criptografado.

### B. Cadeia de Handshake Proativo (Zero-Deadlock)
1. **`SM_INIT` (Opcode `0x00`, 194 bytes)**: Servidor envia chave Blowfish em `0x94`, módulo RSA embaralhado (128 bytes) e flag `0x03`.
2. **`SM_AUTH_GG` (Opcode `0x0B`, 58 bytes wire)**: Servidor envia payload cifrado de verificação GameGuard.
3. **`SM_LOGIN_OK` (Opcode `0x03`, 78 bytes)**: Servidor envia assinatura Classic `0xFF 0xFE` e `TOS_ACCEPTED = 1`.
4. **`SM_SERVER_LIST` (Opcode `0x04`)**: Servidor envia a lista de mundos ativos (Atreia, Bracket 2, porta 7777).
5. **`CM_PLAY` (Opcode `0x02`)**: Cliente solicita entrada no servidor. O servidor gera token na tabela `sessions` e responde com `SM_PLAY_OK` (Opcode `0x07`).

---

## 5. Game Server & Mundo (`Porta 7777`)

* **Tick Rate**: 20.0 TPS fixo com temporizador de alta precisão (`tokio::time::interval`).
* **Sub-sistemas Integrados**:
  * Movimentação, Queda, Voo e Planagem.
  * Combate Físico e Mágico (fórmulas oficiais NCSoft).
  * Inventário, Itens, Equipamentos e Kinah.
  * Spawns e IA de NPCs / Monstros.
  * Trade P2P, Lojas Pessoais e Trocas com NPCs.
  * Títulos, Daeva Pass, Wardrobe e Atreian Passport.

---

## 6. Chat Server (`Porta 10241`)

* **Canais Regionais & Globais**: LFG, Trade, Sanctum, Pandaemonium.
* **Mensagens Privadas (Whispers)** e Gestão de Canais.
* **Proteção Anti-Flood**: Limite de mensagens por segundo configurável.

---

## 7. Supervisor & Dashboard (`Auto-Start EmuRust.exe`)

* **Servidor Web Integrado**: Escuta em `http://0.0.0.0:18080` (Acessível via localhost e remotamente via Wi-Fi/LAN em `http://<LAN-IP>:18080`).
* **Telemetria Day-Trade Real-Time**:
  * Gráfico multicurva estilo TradingView em Canvas 2D de altíssimo desempenho (0.0% CPU ocioso).
  * Curvas individuais: 🔵 Login-Server, 🟢 Game-Server, 🟣 Chat-Server, 🟡 Launcher, ⚪ Total.
  * Níveis de Retração Fibonacci (0.0% a 100.0%) e alternância entre Modo CPU (%) e Modo Memória (MB).
* **Gaveta Lateral Esquerda (Left Drawer)**:
  * Registradores de Sistema: Target TPS (20.0), Tamanho do `aion.db`, Memória Total do SO e Uptime.
  * Mapeamento de Portas (`2106`, `7777`, `10241`, `6600`, `13001`, `18080`).
  * Conexão Mobile LAN com link de 1 clique.
* **Experiência Mobile iOS-Like**:
  * Barra de navegação inferior estilo vidro fosco (`Status`, `Gráfico`, `Logs`, `Menu`).
  * Botão de Ação Flutuante (FAB).
* **Guardião de Instância Silencioso**:
  * Daemons de background (`login-server`, `game-server`, `chat-server`) rodam sem popups modais de bloqueio.
  * Limpeza ativa de processos órfãos (`kill_lingering_processes`) ao inicializar.

---

## 8. Esquema do Banco de Dados SQLite (`aion.db`)

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
    username TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_id INTEGER NOT NULL DEFAULT 1,
    session_key INTEGER NOT NULL DEFAULT 0,
    issued_at INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0,
    expires_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    name TEXT UNIQUE NOT NULL
);
```

---

## 9. Changelog de Correções e Evoluções (Sucessos)

### 12. Overhaul do Dashboard: Gráfico Day-Trade, Mobile iOS, Gaveta Lateral e Daemons Silenciosos
* **Como era antes**: O dashboard possuía margens laterais vazias, botões com emojis unicode, falta de tela cheia nativa e daemons de background exibiam caixas modais `MessageBoxW` invasivas caso houvesse processo órfão anterior.
* **Como foi corrigido**:
  1. Gráfico Day-Trade multicurva em tempo real (Login, Game, Chat, Launcher e Total) com retração Fibonacci e modos CPU/Memória.
  2. Gaveta lateral esquerda (Left Drawer) com Registradores do Sistema, Portas e Acesso Mobile LAN (`http://<LAN-IP>:18080`).
  3. Experiência Mobile responsiva inspirada no iOS (Bottom Tab Bar e FAB).
  4. Ícones substituídos por SVGs vetoriais inline e layout 100% full-width.
  5. `SingleInstanceGuard` refatorado para modo silencioso em daemons, com limpeza proativa de processos órfãos no supervisor.

### 13. Alinhamento da Chave Blowfish em `0x94` e Cadeia de Handshake Proativo
* **Como era antes**: A chave Blowfish estava deslocada no buffer do `SM_INIT` e o servidor aguardava passivamente pelo `CM_AUTH_GG`, gerando deadlock no cliente Gameforge Classic EU.
* **Como foi corrigido**:
  1. Offset da chave Blowfish alinhado rigorosamente no offset `0x94` (índice 148..164) conforme verificado no `game.dll:0x84222D`.
  2. Flag de controle `0xA8` (índice 168) definida como `0x03` conforme `game.dll:0x84231B`.
  3. Cadeia de handshake configurada para empurrar proativamente `SM_AUTH_GG`, `SM_LOGIN_OK` e `SM_SERVER_LIST`, garantindo ativação imediata da interface sem congelamentos.
