# PLAN-11: Trade Broker Global (S_GLOBAL_TRADE_LIST 0x13C, S_GLOBAL_TRADE_SALESLOG 0x141, etc.)

**Status:** `[ ]`  
**Prioridade:** MÉDIA — 56 pacotes capturados: listagem, histórico, commit, estado.

---

## Contexto da Captura Wireshark

**Opcodes capturados:**
- Cliente → Servidor: `C_GLOBAL_TRADE_SALESLOG` (0x101), `C_GLOBAL_TRADE_AVG_PRICE` (0x103)
- Servidor → Cliente: `S_GLOBAL_TRADE_LIST` (0x13C), `S_GLOBAL_TRADE_SALESLOG` (0x141), `S_GLOBAL_TRADE_COMMIT` (0x13F), `S_GLOBAL_TRADE_HISTORY` (0x145), `S_GLOBAL_TRADE_STATE` (0x144)

---

### C_GLOBAL_TRADE_SALESLOG (0x101) — consultar histórico de vendas

```
[u32 item_template_id]
[u8  quality]          — 0-6 (common/uncommon/rare/unique/heroic/fabled/eternal)
[u32 page]             — paginação (0-based)
```

### C_GLOBAL_TRADE_AVG_PRICE (0x103) — consultar preço médio

```
[u32 item_template_id]
[u8  quality]
```

### S_GLOBAL_TRADE_LIST (0x13C) — listagem de itens no broker

```
[u32 total_count]
[u8  page_size]        — itens por página (ex: 20)
[u32 page]
-- para cada entrada:
  [u32 listing_id]
  [u32 item_template_id]
  [u32 quantity]
  [u64 price_per_unit]
  [u16 seller_name_len]
  [u8* seller_name]    — UTF-16LE
  [u64 expiry_timestamp]
  [u8  quality]
  [u8  enhance_level]
```

### S_GLOBAL_TRADE_SALESLOG (0x141) — histórico de vendas recentes

```
[u16 entry_count]
-- para cada entrada:
  [u32 item_template_id]
  [u32 quantity]
  [u64 price]
  [u64 timestamp]
  [u8  quality]
```

### S_GLOBAL_TRADE_COMMIT (0x13F) — confirmação de ação no broker

```
[u8  result]       — 0=sucesso, 1=falha (itens esgotados, etc)
[u32 listing_id]
[u64 kinah_received]
```

### S_GLOBAL_TRADE_HISTORY (0x145) — histórico de transações do jogador

```
[u16 count]
-- para cada transação:
  [u32 item_template_id]
  [u32 quantity]
  [u64 price]
  [u64 timestamp]
  [u8  type]     — 0=venda, 1=compra
```

### S_GLOBAL_TRADE_STATE (0x144) — estado do broker para o jogador

```
[u8  broker_fee_percent]  — taxa do broker (ex: 5 = 5%)
[u64 kinah_pending]       — kinah de vendas não coletado
[u8  active_listings]     — número de listings ativos
[u8  max_listings]        — máximo permitido
```

---

## Estado Atual do Código

**`game-server/src/game/broker.rs`:** Estruturas básicas de broker presentes mas não conectadas ao pipeline de pacotes.  
**Nenhum** handler para C_GLOBAL_TRADE_* em `client.rs`.  
**Nenhum** S_GLOBAL_TRADE_* em `server.rs`.

---

## Tarefas

### 1. Adicionar handlers em client.rs

```rust
define_messages!(
    (GLOBAL_TRADE_SALESLOG, GlobalTradeSaleslog, 0x101),
    (GLOBAL_TRADE_AVG_PRICE, GlobalTradeAvgPrice, 0x103),
    (GLOBAL_TRADE_BUY, GlobalTradeBuy, 0x102),   // verificar opcode exato na captura
    (GLOBAL_TRADE_REGISTER, GlobalTradeRegister, 0x100), // verificar opcode
);
```

### 2. Adicionar S_GLOBAL_TRADE_* em server.rs

```rust
const GLOBAL_TRADE_LIST: u16 = 0x013C;
const GLOBAL_TRADE_SALESLOG: u16 = 0x0141;
const GLOBAL_TRADE_COMMIT: u16 = 0x013F;
const GLOBAL_TRADE_HISTORY: u16 = 0x0145;
const GLOBAL_TRADE_STATE: u16 = 0x0144;
```

### 3. Refatorar broker.rs para integração

```rust
pub struct BrokerListing {
    pub id: u32,
    pub seller_id: u32,
    pub seller_name: String,
    pub item_template_id: u32,
    pub quantity: u32,
    pub price_per_unit: u64,
    pub expiry_ts: u64,
    pub quality: u8,
    pub enhance_level: u8,
}

pub struct BrokerService {
    pub listings: Vec<BrokerListing>,
    pub sales_log: Vec<SalesLogEntry>,
    broker_fee_percent: u8,
}

impl BrokerService {
    pub fn list_items(&self, page: u32, page_size: u32) -> Vec<&BrokerListing>;
    pub fn buy(&mut self, listing_id: u32, buyer_id: u32, buyer_name: &str) -> Result<u64, &str>;
    pub fn register_listing(&mut self, listing: BrokerListing) -> u32;
    pub fn get_avg_price(&self, template_id: u32, quality: u8) -> u64;
    pub fn get_player_history(&self, player_id: u32) -> Vec<&SalesLogEntry>;
    pub fn get_player_state(&self, player_id: u32) -> BrokerPlayerState;
}
```

### 4. Tabelas no banco de dados

```sql
CREATE TABLE IF NOT EXISTS broker_listings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id       INTEGER NOT NULL,
    seller_name     TEXT NOT NULL,
    item_template_id INTEGER NOT NULL,
    quantity        INTEGER NOT NULL,
    price_per_unit  INTEGER NOT NULL,
    expiry_ts       INTEGER NOT NULL,
    quality         INTEGER NOT NULL DEFAULT 0,
    enhance_level   INTEGER NOT NULL DEFAULT 0,
    is_sold         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS broker_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL,
    item_template_id INTEGER NOT NULL,
    quantity        INTEGER NOT NULL,
    price           INTEGER NOT NULL,
    timestamp       INTEGER NOT NULL,
    type            INTEGER NOT NULL  -- 0=venda, 1=compra
);
```

### 5. Handler de GlobalTradeSaleslog no state.rs

```rust
c::Message::GlobalTradeSaleslog(msg) => {
    let log = self.game_data.broker.get_sales_log(
        msg.item_template_id, msg.quality, msg.page
    );
    messages.push_direct(update.client_id(), ServerUpdate::new(
        s::Message::GlobalTradeSaleslog(s::GlobalTradeSaleslog::from(log))
    ));
}
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Adicionar C_GLOBAL_TRADE_* |
| `game-server/src/game/message/server.rs` | Adicionar todos S_GLOBAL_TRADE_* |
| `game-server/src/game/broker.rs` | Refatorar para integração com state |
| `game-server/src/game/state.rs` | Handlers de GlobalTrade* |
| `game-server/src/db.rs` | CRUD para broker_listings e broker_history |

---

## Verificação

- Abrir broker → S_GLOBAL_TRADE_LIST e S_GLOBAL_TRADE_STATE chegam.
- Pesquisar preço médio → S_GLOBAL_TRADE_SALESLOG com histórico.
- Comprar item → S_GLOBAL_TRADE_COMMIT com resultado.
- Vender item → listing aparece para outros jogadores.

---

**Commit:** `git add -A && git commit -m "PLAN-11: Trade Broker — S_GLOBAL_TRADE_LIST, SALESLOG, COMMIT, HISTORY, STATE implementados"`
