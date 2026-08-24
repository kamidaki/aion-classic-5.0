# PLAN-07: Inventário e Equipamentos (SM_INVENTORY_INFO 0x1A, C_EQUIP_ITEM 0x26, SM_UPDATE_PLAYER_APPEARANCE 0x24)

**Status:** `[ ]`  
**Prioridade:** ALTA — equipamentos afetam aparência e stats diretamente.

---

## Contexto da Captura Wireshark

### SM_INVENTORY_INFO (0x1A) — carga inicial do inventário (login)

Formato de cada item na Cube:
```
[u32 item_unique_id]       — ID único do item na instância do jogador
[u32 item_template_id]     — ID do template do item (do XML items.xml)
[u32 slot]                 — slot no inventário (0-based dentro da Cube)
[u32 quantity]
[u8  enhance_level]        — nível de enchant (+0 a +15)
[u8  rune_count]           — número de runas inseridas
[u32 rune_slot_1]          — item_id da runa (0 se vazio)
[u32 rune_slot_2]
[u32 rune_slot_3]
[u32 rune_slot_4]
[u8  is_equipped]          — 1 se equipado
[u32 equip_slot]           — slot de equipamento (ver enum abaixo)
[u64 kinah_in_slot]        — só para slot de kinah
```

**Enum de slots de equipamento (verificados na captura):**
```
0  = MainHand (arma principal)
1  = SubHand (escudo/off-hand)
2  = Head
3  = Chest (torso)
4  = Legs (calças)
5  = Boots
6  = Gloves
7  = Shoulder
8  = Back (manto)
9  = Neck
10 = RingLeft
11 = RingRight
12 = EarLeft
13 = EarRight
14 = Belt
15 = Wings
```

### C_EQUIP_ITEM (0x26) — equipar/desequipar

```
[u32 item_unique_id]
[u8  equip_action]    — 0=equipar, 1=desequipar
[u32 equip_slot]      — slot alvo (enum acima)
```

### SM_UPDATE_PLAYER_APPEARANCE (0x24) — atualizar visual para outros jogadores

```
[u32 player_id]
[u32 item_ids[16]]    — template_id de cada slot (0 se vazio)
                        índices = enum de equip_slot acima
```

---

## Estado Atual do Código

**`server.rs`:** `CarregaInventario45` presente mas estrutura incompleta — falta `enhance_level`, `rune_count`, `rune_slots`, `equip_slot`.  
**`client.rs`:** `UseEquipmentItem` (0x26) implementado — mas handler não atualiza `SM_UPDATE_PLAYER_APPEARANCE`.  
**`state.rs`:** `respond()` para UseEquipmentItem emite `ChangeItemDesc` mas não broadcast da aparência.  
**`character.rs`:** `Character` tem `equipment` mas sem métodos `equip()`/`unequip()` que calculem stat changes.

---

## Tarefas

### 1. Corrigir SM_INVENTORY_INFO (0x1A) em server.rs

```rust
pub struct InventoryItem {
    pub unique_id: u32,
    pub template_id: u32,
    pub slot: u32,
    pub quantity: u32,
    pub enhance_level: u8,
    pub rune_count: u8,
    pub rune_slots: [u32; 4],
    pub is_equipped: u8,
    pub equip_slot: u32,
    pub kinah: u64,
}

pub struct LoadInventory {
    pub cube_size: u32,   // tamanho total da Cube (ex: 27 padrão)
    pub items: Vec<InventoryItem>,
}

impl Serialise for LoadInventory {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, LOAD_INVENTORY, &mut ptr);
        to_le_bytes!(ptr, buf, self.cube_size);
        to_le_bytes!(ptr, buf, self.items.len() as u32);
        for item in &self.items {
            to_le_bytes!(ptr, buf, item.unique_id);
            to_le_bytes!(ptr, buf, item.template_id);
            to_le_bytes!(ptr, buf, item.slot);
            to_le_bytes!(ptr, buf, item.quantity);
            buf[ptr] = item.enhance_level; ptr += 1;
            buf[ptr] = item.rune_count; ptr += 1;
            for r in &item.rune_slots { to_le_bytes!(ptr, buf, r); }
            buf[ptr] = item.is_equipped; ptr += 1;
            to_le_bytes!(ptr, buf, item.equip_slot);
            to_le_bytes!(ptr, buf, item.kinah);
        }
        prepend_length(buf, ptr)
    }
}
```

### 2. Corrigir SM_UPDATE_PLAYER_APPEARANCE (0x24) em server.rs

```rust
const UPDATE_PLAYER_APPEARANCE: u16 = 0x0024;

pub struct UpdatePlayerAppearance {
    pub player_id: u32,
    pub items: [u32; 16],  // template_id por slot (0=vazio)
}

impl Serialise for UpdatePlayerAppearance {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, UPDATE_PLAYER_APPEARANCE, &mut ptr);
        to_le_bytes!(ptr, buf, self.player_id);
        for item in &self.items {
            to_le_bytes!(ptr, buf, item);
        }
        prepend_length(buf, ptr)
    }
}
```

### 3. Implementar equip/unequip no state.rs

```rust
c::Message::UseEquipmentItem(msg) => {
    let char = self.characters.get_mut(&update.character_id())?;
    match msg.action {
        0 => {
            // Equipar
            if let Some(old_item) = char.equip_item(msg.item_unique_id, msg.equip_slot) {
                // old_item foi desequipado para dar lugar
            }
        }
        1 => {
            // Desequipar
            char.unequip_slot(msg.equip_slot);
        }
        _ => {}
    }
    // Recalcular stats
    let new_stats = char.recalculate_stats(&self.game_data);
    // Emitir S_STATS_INFO atualizado (direct)
    messages.push_direct(update.client_id(), ServerUpdate::new(
        s::Message::Status(s::Status::from_character(char, &new_stats))
    ));
    // Broadcast aparência para outros jogadores
    messages.push_others(update.client_id(), ServerUpdate::new(
        s::Message::UpdatePlayerAppearance(s::UpdatePlayerAppearance {
            player_id: char.id(),
            items: char.equipment_template_ids(),
        })
    ));
    // SM_INVENTORY_INFO atualizado (direct)
    messages.push_direct(update.client_id(), ServerUpdate::new(
        s::Message::LoadInventory(char.build_inventory_packet())
    ));
}
```

### 4. Métodos em character.rs

```rust
impl Character {
    pub fn equip_item(&mut self, unique_id: u32, equip_slot: u32) -> Option<u32>;
    pub fn unequip_slot(&mut self, equip_slot: u32);
    pub fn equipment_template_ids(&self) -> [u32; 16];
    pub fn recalculate_stats(&mut self, game_data: &GameData) -> Stats;
    pub fn build_inventory_packet(&self) -> LoadInventory;
}
```

### 5. Persistir equipamentos no banco

```sql
ALTER TABLE players ADD COLUMN equipped_items TEXT DEFAULT '{}';
-- JSON map: equip_slot -> item_unique_id
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Corrigir `LoadInventory`, adicionar `UpdatePlayerAppearance` (0x24) |
| `game-server/src/game/message/client.rs` | Verificar estrutura de `UseEquipmentItem` (0x26) |
| `game-server/src/game/state.rs` | Handler de UseEquipmentItem completo com stat recalc |
| `game-server/src/game/character.rs` | Métodos equip/unequip/stats |
| `game-server/src/db.rs` | Persistência de equipamentos e inventário |
| `game-server/src/game/data/item.rs` | Adicionar campos de stat por item template |

---

## Verificação

- Login → SM_INVENTORY_INFO deve listar todos os itens com enhance e runas.
- Equipar item → stats mudam, SM_UPDATE_PLAYER_APPEARANCE chega para outros players.
- Desequipar → item volta ao inventário, visual atualizado.

---

**Commit:** `git add -A && git commit -m "PLAN-07: SM_INVENTORY_INFO completo com runas/enhance, C_EQUIP_ITEM com stat recalc, SM_UPDATE_PLAYER_APPEARANCE broadcast"`
