# PLAN-09: Legião/Guild (S_GUILD_INFO 0x06D, S_GUILD_MEMBER_INFO 0x09C, Emblema 0x0D5, Buffs, Doações)

**Status:** `[x]`  
**Prioridade:** MÉDIA — 2.565 pacotes capturados cobrindo ciclo de vida completo.

---

## Contexto da Captura Wireshark

**Opcodes capturados:**
- Cliente → Servidor: `C_REQUEST_GUILD_HISTORY` (57x), `C_GUILD_USER_BUY_BUFF` (10x), `C_GUILD` (5x), `C_GUILD_REQUEST_OPEN_BUFF`
- Servidor → Cliente: `S_GUILD_INFO` (0x06D), `S_GUILD_MEMBER_INFO` (0x09C), `S_ADD_GUILD_MEMBER`, `S_USER_GUILD_DONATION` (0x158), `S_USER_GUILD_DONATION_LIST` (0x159), `S_USER_GUILD_COIN` (0x165), `S_GUILD_DONATION` (0x157), `S_GUILD_EMBLEM_IMG_DATA` (0x0D5 — **51 pacotes para um emblema**), `S_GUILD_OPENED_BUFF_TREE_INFO`, `S_GUILD_CRAFT`

---

### S_GUILD_INFO (0x06D) — informações da legião

```
[u32 guild_id]
[u16 name_len]
[u8* guild_name]           — UTF-16LE
[u8  rank]                 — grau (1–10)
[u8  race]                 — 0=Elyos, 1=Asmodian
[u32 exp]                  — pontos de experiência da legião
[u32 contribution_points]
[u16 member_count]
[u16 member_max]           — máximo de membros (30 padrão)
[u32 leader_id]
[u16 notice_len]
[u8* notice]               — anúncio da legião UTF-16LE
[u64 kinah]                — cofre da legião
```

### S_GUILD_MEMBER_INFO (0x09C) — informações de um membro

```
[u32 guild_id]
[u32 member_id]
[u8  guild_rank_index]     — posição hierárquica na legião
[u16 name_len]
[u8* name]                 — UTF-16LE
[u8  class_id]
[u8  level]
[u8  race]
[u8  is_online]            — 0 ou 1
[u32 last_online_timestamp]
[u64 contribution]         — contribuição acumulada
[u32 map_id]               — mapa onde está o membro
```

### S_GUILD_EMBLEM_IMG_DATA (0x0D5) — download de emblema em chunks

O emblema é enviado em **51 pacotes** de aproximadamente 512 bytes de dados cada.

```
[u32 guild_id]
[u16 chunk_index]          — índice do chunk (0-based)
[u16 total_chunks]         — total de chunks (51)
[u16 data_len]
[u8* data]                 — bytes do PNG do emblema
```

### S_USER_GUILD_DONATION (0x158) — estado de doação do jogador

```
[u32 player_id]
[u64 daily_donated]
[u64 daily_limit]
[u64 total_donated]
[u32 last_donation_timestamp]
```

### S_USER_GUILD_COIN (0x165) — moedas de legião do jogador

```
[u32 player_id]
[u64 coin_amount]
```

### S_GUILD_OPENED_BUFF_TREE_INFO — buffs ativos da árvore de legião

```
[u32 guild_id]
[u8  buff_count]
-- para cada buff:
  [u32 buff_id]
  [u32 duration_remaining_ms]
  [u32 level]
```

---

## Estado Atual do Código

**Nenhum** handler de guild/legião em `client.rs` ou `server.rs`. Os módulos relevantes não existem como sistema integrado.  
**`social.rs`:** Tem enum de canais de chat mas nada de guild.

---

## Tarefas

### 1. Criar game-server/src/game/guild.rs

```rust
#[derive(Debug, Clone)]
pub struct Guild {
    pub id: u32,
    pub name: String,
    pub rank: u8,          // 1-10
    pub race: u8,
    pub exp: u32,
    pub contribution_points: u32,
    pub leader_id: u32,
    pub notice: String,
    pub kinah: u64,
    pub members: Vec<GuildMember>,
    pub emblem_png: Option<Vec<u8>>,
    pub active_buffs: Vec<GuildBuff>,
}

#[derive(Debug, Clone)]
pub struct GuildMember {
    pub player_id: u32,
    pub name: String,
    pub guild_rank_index: u8,
    pub class_id: u8,
    pub level: u8,
    pub race: u8,
    pub is_online: bool,
    pub last_online: u32,
    pub contribution: u64,
    pub map_id: u32,
}

#[derive(Debug, Clone)]
pub struct GuildBuff {
    pub buff_id: u32,
    pub remaining_ms: u32,
    pub level: u32,
}
```

### 2. Adicionar S_GUILD_INFO (0x06D) em server.rs

```rust
const GUILD_INFO: u16 = 0x006D;
// Serialise seguindo estrutura acima
```

### 3. Adicionar S_GUILD_MEMBER_INFO (0x09C) em server.rs

```rust
const GUILD_MEMBER_INFO: u16 = 0x009C;
```

### 4. Implementar S_GUILD_EMBLEM_IMG_DATA (0x0D5) — chunked

```rust
const GUILD_EMBLEM_IMG_DATA: u16 = 0x00D5;
const CHUNK_SIZE: usize = 512;

pub fn build_emblem_packets(guild_id: u32, png_data: &[u8]) -> Vec<s::Message> {
    let total_chunks = (png_data.len() + CHUNK_SIZE - 1) / CHUNK_SIZE;
    png_data.chunks(CHUNK_SIZE)
        .enumerate()
        .map(|(i, chunk)| s::Message::GuildEmblemImgData(GuildEmblemImgData {
            guild_id,
            chunk_index: i as u16,
            total_chunks: total_chunks as u16,
            data: chunk.to_vec(),
        }))
        .collect()
}
```

### 5. Adicionar handlers C_GUILD* em client.rs

```rust
define_messages!(
    (REQUEST_GUILD_HISTORY, RequestGuildHistory, 0xC_OPCODE), // verificar opcode exato
    (GUILD_USER_BUY_BUFF, GuildUserBuyBuff, 0xD_OPCODE),
);
```

### 6. Emitir info de legião no spawn

Após C_LEVEL_READY, se personagem tem legião:
1. `S_GUILD_INFO` (direct)
2. `S_GUILD_MEMBER_INFO` para cada membro (direct)
3. `S_USER_GUILD_COIN` (direct)
4. `S_USER_GUILD_DONATION` (direct)
5. `S_GUILD_OPENED_BUFF_TREE_INFO` (direct)

### 7. Tabelas no banco de dados

```sql
CREATE TABLE IF NOT EXISTS guilds (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT UNIQUE NOT NULL,
    rank     INTEGER NOT NULL DEFAULT 1,
    race     INTEGER NOT NULL DEFAULT 0,
    exp      INTEGER NOT NULL DEFAULT 0,
    leader_id INTEGER NOT NULL,
    notice   TEXT NOT NULL DEFAULT '',
    kinah    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id    INTEGER NOT NULL,
    player_id   INTEGER NOT NULL,
    rank_index  INTEGER NOT NULL DEFAULT 5,
    contribution INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, player_id),
    FOREIGN KEY (guild_id) REFERENCES guilds(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/guild.rs` | Criar novo arquivo com estruturas de guild |
| `game-server/src/game/message/server.rs` | Adicionar todos os S_GUILD_* |
| `game-server/src/game/message/client.rs` | Adicionar handlers C_GUILD_* |
| `game-server/src/game/state.rs` | Integrar guild info no spawn, handlers de C_GUILD |
| `game-server/src/game/mod.rs` | Adicionar `pub mod guild;` |
| `game-server/src/db.rs` | CRUD para guilds e guild_members |

---

## Verificação

- Jogador com legião → ao entrar recebe S_GUILD_INFO e lista de membros.
- Emblema → 51 chunks chegam ao cliente e emblema renderiza.
- Aba de doação → S_USER_GUILD_DONATION e S_USER_GUILD_COIN corretos.
- Buffs de legião → S_GUILD_OPENED_BUFF_TREE_INFO com buffs ativos.

---

**Commit:** `git add -A && git commit -m "PLAN-09: Legião — S_GUILD_INFO, S_GUILD_MEMBER_INFO, emblema chunked 51 pacotes, doações, moedas, buffs"`
