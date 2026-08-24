# PLAN-10: Social — Grupo, Trade P2P, Aliança e Amigos

**Status:** `[ ]`  
**Prioridade:** MÉDIA — C_PARTY (0x060), C_ADD_BUDDY (0x06F), S_BUDDY_LIST (0x083), S_ALLIANCE_INFO (0x0F5).

---

## Contexto da Captura Wireshark

Opcodes: `C_PARTY` (0x060), `C_PARTY_BY_NAME` (0x061), `C_ADD_BUDDY` (0x06F), `S_BUDDY_LIST` (0x083), `S_ALLIANCE_INFO` (0x0F5), `S_ALLIANCE_MEMBER_INFO` (0x0F6), `S_PARTY_MATCH` (0x0A5), `S_MESSAGE_CODE` (para recusas).

---

### C_PARTY (0x060) — convidar jogador para grupo por ID

```
[u32 target_player_id]
[u8  action]   — 0=convidar, 1=aceitar, 2=recusar, 3=sair, 4=expulsar
```

### C_PARTY_BY_NAME (0x061) — convidar por nome

```
[u16 name_len]
[u8* name]    — UTF-16LE
```

### C_ADD_BUDDY (0x06F) — adicionar amigo

```
[u16 name_len]
[u8* name]    — UTF-16LE
[u8  action]  — 0=adicionar, 1=remover
```

### S_BUDDY_LIST (0x083) — lista de amigos

```
[u16 buddy_count]
-- para cada amigo:
  [u32 player_id]
  [u16 name_len]
  [u8* name]
  [u8  is_online]     — 0 ou 1
  [u32 map_id]        — 0 se offline
  [u8  level]
  [u8  class_id]
```

### S_ALLIANCE_INFO (0x0F5) — informações da aliança

```
[u32 alliance_id]
[u16 name_len]
[u8* name]
[u32 leader_id]
[u8  member_count]    — total de membros (grupos combinados)
```

### S_ALLIANCE_MEMBER_INFO (0x0F6) — membro da aliança

```
[u32 alliance_id]
[u32 player_id]
[u8  group_index]     — qual grupo (0-5) dentro da aliança
[u16 name_len]
[u8* name]
[u32 hp_current]
[u32 hp_max]
[u32 mp_current]
[u32 mp_max]
[u8  level]
[u8  class_id]
[u8  is_online]
```

### S_PARTY_MATCH (0x0A5) — matchmaking de grupo aberto

```
[u32 match_id]
[u8  status]     — 0=disponível, 1=cheio
[u8  member_count]
[u8  min_level]
[u8  max_level]
[u16 desc_len]
[u8* desc]
```

### S_MESSAGE_CODE — resposta de recusa/cancelamento

```
[u32 message_code]   — ex: 900001=convite recusado, 900002=jogador offline
[u32 player_id]      — quem recusou
```

---

## Estado Atual do Código

**`social.rs`:** Tem enums `ChatChannel` e `GmCommand`, `resolve_goto_location`. Nenhum sistema de party/buddy.  
**`client.rs`:** `QueryBuddy` (0x6E) presente mas handler vazio.  
**`server.rs`:** `BuddyList` (0x083) presente mas vazio — serializa 0 amigos.

---

## Tarefas

### 1. Adicionar handlers em client.rs

```rust
define_messages!(
    (PARTY, Party, 0x60),
    (PARTY_BY_NAME, PartyByName, 0x61),
    (ADD_BUDDY, AddBuddy, 0x6F),
);
```

### 2. Corrigir S_BUDDY_LIST (0x083) em server.rs

```rust
pub struct BuddyEntry {
    pub player_id: u32,
    pub name: String,
    pub is_online: bool,
    pub map_id: u32,
    pub level: u8,
    pub class_id: u8,
}

pub struct BuddyList {
    pub buddies: Vec<BuddyEntry>,
}

impl Serialise for BuddyList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, BUDDY_LIST, &mut ptr);
        to_le_bytes!(ptr, buf, self.buddies.len() as u16);
        for b in &self.buddies {
            to_le_bytes!(ptr, buf, b.player_id);
            let name_utf16 = encode_utf16le(&b.name);
            to_le_bytes!(ptr, buf, name_utf16.len() as u16);
            copy_bytes!(ptr, buf, name_utf16);
            buf[ptr] = b.is_online as u8; ptr += 1;
            to_le_bytes!(ptr, buf, b.map_id);
            buf[ptr] = b.level; ptr += 1;
            buf[ptr] = b.class_id; ptr += 1;
        }
        prepend_length(buf, ptr)
    }
}
```

### 3. Adicionar S_ALLIANCE_INFO (0x0F5) e S_ALLIANCE_MEMBER_INFO (0x0F6)

### 4. Implementar sistema de grupo em social.rs

```rust
#[derive(Debug, Clone)]
pub struct PartyGroup {
    pub id: u32,
    pub leader_id: u32,
    pub members: Vec<u32>,  // player_ids
    pub loot_type: u8,      // 0=round-robin, 1=leader
}

pub struct PartyService {
    pub groups: HashMap<u32, PartyGroup>,
    next_id: u32,
}

impl PartyService {
    pub fn invite(&mut self, from: u32, to: u32) -> u32; // retorna group_id
    pub fn accept(&mut self, group_id: u32, player_id: u32);
    pub fn leave(&mut self, player_id: u32);
    pub fn group_of(&self, player_id: u32) -> Option<u32>;
}
```

### 5. Emitir S_BUDDY_LIST no spawn

```rust
// Após C_LEVEL_READY:
let buddies = self.db.load_buddies(char.id());
messages.push_direct(client_id, s::Message::BuddyList(
    s::BuddyList::from_entries(buddies, &online_players)
));
```

### 6. Handler de AddBuddy no state.rs

```rust
c::Message::AddBuddy(msg) => {
    match msg.action {
        0 => {
            // Adicionar: verificar se jogador existe
            if let Some(target) = self.db.find_player_by_name(&msg.name) {
                self.db.add_buddy(update.character_id(), target.id);
                // Re-enviar S_BUDDY_LIST atualizado
            } else {
                // Emitir S_MESSAGE_CODE com "jogador não encontrado"
            }
        }
        1 => {
            // Remover amigo
            self.db.remove_buddy(update.character_id(), msg.name);
        }
        _ => {}
    }
}
```

### 7. Tabelas no banco de dados

```sql
CREATE TABLE IF NOT EXISTS character_buddies (
    player_id  INTEGER NOT NULL,
    buddy_id   INTEGER NOT NULL,
    PRIMARY KEY (player_id, buddy_id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Adicionar `Party`, `PartyByName`, `AddBuddy` |
| `game-server/src/game/message/server.rs` | Corrigir `BuddyList`, adicionar `AllianceInfo`, `AllianceMemberInfo` |
| `game-server/src/game/social.rs` | Adicionar `PartyService` e `PartyGroup` |
| `game-server/src/game/state.rs` | Handlers de Party e AddBuddy |
| `game-server/src/db.rs` | CRUD para buddies e parties |

---

## Verificação

- Login → S_BUDDY_LIST correto com amigos online/offline.
- Convidar jogador → notificação de convite, aceitar/recusar funcional.
- Grupo formado → membros compartilham HP bars.
- Adicionar amigo → aparece na lista, remover também funcional.

---

**Commit:** `git add -A && git commit -m "PLAN-10: Social — S_BUDDY_LIST corrigido, PartyService, S_ALLIANCE_INFO, S_ALLIANCE_MEMBER_INFO"`
