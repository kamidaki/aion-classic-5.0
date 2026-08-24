# PLAN-13: Banco de Dados SQLite — Schema Completo e Migrações

**Status:** `[x]`  
**Prioridade:** FUNDAÇÃO — todos os outros planos dependem de um schema correto.

---

## Estado Atual

O schema atual (`CONTEXT.md`, seção 8) tem apenas 3 tabelas:
- `accounts`: login básico
- `sessions`: tokens de sessão
- `players`: id, account_name, name — **sem stats, posição, classe, nível, inventário, quests, etc.**

**Problema crítico:** A tabela `players` não tem os campos necessários para persistir um personagem real. Isso significa que a cada reinício do servidor o personagem perde posição, nível, inventário, quests e todos os progressos.

---

## Schema Completo Alvo

### Tabela `players` (expandida)

```sql
CREATE TABLE IF NOT EXISTS players (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name    TEXT NOT NULL,
    name            TEXT UNIQUE NOT NULL,
    
    -- Identidade
    race            INTEGER NOT NULL DEFAULT 0,   -- 0=Elyos, 1=Asmodian
    gender          INTEGER NOT NULL DEFAULT 0,   -- 0=male, 1=female
    class_id        INTEGER NOT NULL DEFAULT 0,
    
    -- Progressão
    level           INTEGER NOT NULL DEFAULT 1,
    exp             INTEGER NOT NULL DEFAULT 0,
    dp              INTEGER NOT NULL DEFAULT 0,
    ap              INTEGER NOT NULL DEFAULT 0,   -- Abyss Points
    
    -- Recursos
    hp_current      INTEGER NOT NULL DEFAULT 700,
    mp_current      INTEGER NOT NULL DEFAULT 300,
    
    -- Localização
    map_id          INTEGER NOT NULL DEFAULT 110070000,  -- Kaisinel Academy
    x               REAL NOT NULL DEFAULT 457.0,
    y               REAL NOT NULL DEFAULT 251.0,
    z               REAL NOT NULL DEFAULT 127.04,
    heading         INTEGER NOT NULL DEFAULT 0,
    
    -- Social
    guild_id        INTEGER,
    title_id        INTEGER NOT NULL DEFAULT 0,
    
    -- Metadados
    access_level    INTEGER NOT NULL DEFAULT 0,
    created_at      INTEGER NOT NULL DEFAULT 0,
    last_online     INTEGER NOT NULL DEFAULT 0,
    
    -- Aparência (JSON compacto: face/hair/voice indices)
    appearance      TEXT NOT NULL DEFAULT '{}',
    
    FOREIGN KEY (account_name) REFERENCES accounts(name)
);
```

### Tabela `character_inventory` (nova)

```sql
CREATE TABLE IF NOT EXISTS character_inventory (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id      INTEGER NOT NULL,
    item_template_id  INTEGER NOT NULL,
    unique_id         INTEGER NOT NULL,          -- UUID único do item
    slot              INTEGER NOT NULL DEFAULT -1, -- -1 = não equipado
    quantity          INTEGER NOT NULL DEFAULT 1,
    enhance_level     INTEGER NOT NULL DEFAULT 0,
    rune_slot_1       INTEGER NOT NULL DEFAULT 0,
    rune_slot_2       INTEGER NOT NULL DEFAULT 0,
    rune_slot_3       INTEGER NOT NULL DEFAULT 0,
    rune_slot_4       INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES players(id)
);
CREATE INDEX idx_char_inv ON character_inventory(character_id);
```

### Tabela `character_skills` (nova)

```sql
CREATE TABLE IF NOT EXISTS character_skills (
    character_id  INTEGER NOT NULL,
    skill_id      INTEGER NOT NULL,
    skill_level   INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (character_id, skill_id),
    FOREIGN KEY (character_id) REFERENCES players(id)
);
```

### Tabela `character_quests` (nova)

```sql
CREATE TABLE IF NOT EXISTS character_quests (
    character_id  INTEGER NOT NULL,
    quest_id      INTEGER NOT NULL,
    status        INTEGER NOT NULL DEFAULT 0,    -- 0=ativa, 1=completa, 2=entregue
    flags         INTEGER NOT NULL DEFAULT 0,
    var1          INTEGER NOT NULL DEFAULT 0,
    var2          INTEGER NOT NULL DEFAULT 0,
    var3          INTEGER NOT NULL DEFAULT 0,
    var4          INTEGER NOT NULL DEFAULT 0,
    start_ts      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (character_id, quest_id),
    FOREIGN KEY (character_id) REFERENCES players(id)
);
```

### Tabela `character_mail` (nova — ver PLAN-08)

```sql
CREATE TABLE IF NOT EXISTS character_mail (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id     INTEGER NOT NULL,
    sender_id        INTEGER NOT NULL DEFAULT 0,
    sender_name      TEXT NOT NULL DEFAULT 'System',
    title            TEXT NOT NULL DEFAULT '',
    body             TEXT NOT NULL DEFAULT '',
    letter_type      INTEGER NOT NULL DEFAULT 0,
    is_read          INTEGER NOT NULL DEFAULT 0,
    has_item         INTEGER NOT NULL DEFAULT 0,
    item_template_id INTEGER NOT NULL DEFAULT 0,
    item_quantity    INTEGER NOT NULL DEFAULT 0,
    kinah_amount     INTEGER NOT NULL DEFAULT 0,
    timestamp        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (recipient_id) REFERENCES players(id)
);
```

### Tabela `guilds` (nova — ver PLAN-09)

```sql
CREATE TABLE IF NOT EXISTS guilds (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT UNIQUE NOT NULL,
    rank      INTEGER NOT NULL DEFAULT 1,
    race      INTEGER NOT NULL DEFAULT 0,
    exp       INTEGER NOT NULL DEFAULT 0,
    leader_id INTEGER NOT NULL,
    notice    TEXT NOT NULL DEFAULT '',
    kinah     INTEGER NOT NULL DEFAULT 0,
    emblem    BLOB                              -- PNG do emblema
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id     INTEGER NOT NULL,
    player_id    INTEGER NOT NULL,
    rank_index   INTEGER NOT NULL DEFAULT 5,
    contribution INTEGER NOT NULL DEFAULT 0,
    join_ts      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, player_id)
);
```

### Tabela `character_buddies` (nova — ver PLAN-10)

```sql
CREATE TABLE IF NOT EXISTS character_buddies (
    player_id INTEGER NOT NULL,
    buddy_id  INTEGER NOT NULL,
    added_ts  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, buddy_id)
);
```

### Tabela `broker_listings` (nova — ver PLAN-11)

```sql
CREATE TABLE IF NOT EXISTS broker_listings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id        INTEGER NOT NULL,
    seller_name      TEXT NOT NULL,
    item_template_id INTEGER NOT NULL,
    quantity         INTEGER NOT NULL,
    price_per_unit   INTEGER NOT NULL,
    expiry_ts        INTEGER NOT NULL,
    quality          INTEGER NOT NULL DEFAULT 0,
    enhance_level    INTEGER NOT NULL DEFAULT 0,
    is_sold          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS broker_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id        INTEGER NOT NULL,
    item_template_id INTEGER NOT NULL,
    quantity         INTEGER NOT NULL,
    price            INTEGER NOT NULL,
    timestamp        INTEGER NOT NULL,
    tx_type          INTEGER NOT NULL  -- 0=venda, 1=compra
);
```

---

## Tarefas

### 1. Criar migration system em db.rs

```rust
impl Db {
    pub fn migrate(&self) -> rusqlite::Result<()> {
        self.conn.execute_batch("
            PRAGMA journal_mode = WAL;
            PRAGMA busy_timeout = 5000;
            PRAGMA synchronous = NORMAL;
            PRAGMA foreign_keys = ON;
        ")?;
        self.create_tables()?;
        self.migrate_v1_to_v2()?;  // adicionar colunas ausentes
        Ok(())
    }
    
    fn migrate_v1_to_v2(&self) -> rusqlite::Result<()> {
        // ALTER TABLE players ADD COLUMN se não existir
        // Usar "PRAGMA table_info(players)" para verificar
    }
}
```

### 2. Implementar todos os métodos CRUD ausentes

```rust
impl Db {
    // Personagem
    pub fn save_character_full(&self, character: &Character) -> rusqlite::Result<()>;
    pub fn load_character(&self, id: u32) -> rusqlite::Result<Option<CharacterData>>;
    pub fn load_characters_for_account(&self, account: &str) -> rusqlite::Result<Vec<CharacterData>>;
    
    // Inventário
    pub fn save_inventory(&self, char_id: u32, items: &[InventoryItem]) -> rusqlite::Result<()>;
    pub fn load_inventory(&self, char_id: u32) -> rusqlite::Result<Vec<InventoryItem>>;
    
    // Skills
    pub fn save_skills(&self, char_id: u32, skills: &[Skill]) -> rusqlite::Result<()>;
    pub fn load_skills(&self, char_id: u32) -> rusqlite::Result<Vec<Skill>>;
    
    // Quests
    pub fn save_quest(&self, char_id: u32, quest: &QuestEntry) -> rusqlite::Result<()>;
    pub fn load_quests(&self, char_id: u32) -> rusqlite::Result<Vec<QuestEntry>>;
    
    // Correio
    pub fn load_mail(&self, char_id: u32) -> rusqlite::Result<Vec<MailLetter>>;
    pub fn save_mail(&self, letter: &MailLetter) -> rusqlite::Result<u32>;
    pub fn mark_mail_read(&self, letter_id: u32) -> rusqlite::Result<()>;
    pub fn delete_mail(&self, letter_id: u32) -> rusqlite::Result<()>;
    
    // Buddies
    pub fn load_buddies(&self, char_id: u32) -> rusqlite::Result<Vec<BuddyEntry>>;
    pub fn add_buddy(&self, char_id: u32, buddy_id: u32) -> rusqlite::Result<()>;
    pub fn remove_buddy(&self, char_id: u32, buddy_id: u32) -> rusqlite::Result<()>;
    
    // Guild
    pub fn load_guild(&self, guild_id: u32) -> rusqlite::Result<Option<Guild>>;
    pub fn find_player_by_name(&self, name: &str) -> rusqlite::Result<Option<PlayerBasic>>;
}
```

### 3. Atualizar persist_all() no state.rs

Salvar completamente cada personagem a cada 10 segundos:
- Stats, posição, HP/MP, XP, kinah
- Inventário completo
- Skills ativas
- Quests ativas

### 4. Criar aion.db v2 compatível com v1

O sistema de migration deve:
1. Verificar a versão do schema com `PRAGMA user_version`.
2. Executar ALTER TABLE para cada coluna nova.
3. Criar as novas tabelas.
4. Atualizar `PRAGMA user_version = 2`.

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/db.rs` | Schema completo, migration system, todos os métodos CRUD |
| `game-server/src/game/state.rs` | Usar DB completo no `persist_all()` e no carregamento de personagem |
| `game-server/src/game/character.rs` | Carregar dados completos do banco no spawn |

---

## Verificação

- Reiniciar servidor → personagem aparece na posição onde saiu.
- Inventário persiste entre sessões.
- Quests ativas mantidas.
- Nível e XP mantidos.
- Schema v2 compatível com banco v1 existente (migration sem perda de dados).

---

**Commit:** `git add -A && git commit -m "PLAN-13: Schema SQLite v2 completo — players expandido, inventory, skills, quests, mail, guild, buddies, broker, migration system"`
