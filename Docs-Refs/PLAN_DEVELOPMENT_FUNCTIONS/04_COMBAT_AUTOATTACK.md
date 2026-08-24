# PLAN-04: Combate — Auto-Ataque (C_ATTACK 0x20, S_ATTACK_STATUS 0x05, S_CASTSPELL_RESULT 0x2B)

**Status:** `[ ]`  
**Prioridade:** ALTA — ataque físico automático é a mecânica de combate base.

---

## Contexto da Captura Wireshark

O auto-ataque no Aion Classic é um ciclo: o cliente envia `C_ATTACK` quando inicia o ataque automático. O servidor processa cada hit a cada swing do personagem (speed_attack do personagem) e responde com `S_ATTACK_STATUS` para atualizar o HP do alvo visível a todos.

### C_ATTACK (0x20) — iniciar/parar auto-ataque

```
[u32 target_id]     — 0 = parar auto-ataque
[u8  attack_type]   — 0=normal, 1=off-hand
```

### S_ATTACK_STATUS (0x05) — HP do alvo após hit

```
[u32 entity_id]     — quem tomou dano
[i32 damage]        — quantidade de dano (positivo = dano recebido)
[u32 hp_current]    — HP atual após dano
[u32 hp_max]        — HP máximo
[u8  damage_type]   — 0=físico, 1=mágico, 2=true_damage
[u8  is_critical]   — 0 ou 1
```

### S_CASTSPELL_RESULT (opcode 0x2B no client.rs como SM_CASTSPELL_RESULT)

Usado também para o resultado do auto-ataque em alguns contextos. Verificar na captura se auto-ataque usa 0x05 exclusivamente ou também 0x2B.

### S_STATUPDATE_HP (0x03) — HP do JOGADOR LOCAL

```
[u32 hp_current]
[u32 hp_max]
```

Emitido quando o próprio jogador toma dano.

### S_STATUPDATE_MP (0x04) — MP do JOGADOR LOCAL

```
[u32 mp_current]
[u32 mp_max]
```

---

## Estado Atual do Código

**`client.rs`:** `Attack` (0x20) implementado — chama `tx.send(ClientUpdate)`.  
**`state.rs`:** Handler de `ClientUpdate::Attack` presente.  
**`server.rs`:** `HitPointOther` (0x05) presente.  
**Problema:** O ciclo de auto-ataque não tem timer — o dano é aplicado uma vez mas não repete a cada swing. O campo `is_critical` não está sendo calculado. O `S_STATUPDATE_HP` (0x03) não é enviado quando o jogador toma dano de NPC.

---

## Tarefas

### 1. Implementar ciclo de auto-ataque com timer por personagem (state.rs)

```rust
// No struct State, adicionar:
attack_timers: HashMap<u32, (u32, Instant)>, // character_id -> (target_id, next_swing)

// No update() tick:
for (char_id, (target_id, next_swing)) in &mut self.attack_timers {
    if Instant::now() >= *next_swing {
        let character = self.characters.get(char_id)?;
        let swing_speed_ms = character.attack_speed_ms(); // ex: 1500ms
        *next_swing = Instant::now() + Duration::from_millis(swing_speed_ms as u64);

        // Calcular dano
        let hit = engine::damage::Hit::physical(character, target);
        // Emitir S_ATTACK_STATUS para broadcast
        messages.push_others(*client_id_for(char_id), ServerUpdate::new(
            s::Message::HitPointOther(s::HitPointOther {
                entity_id: *target_id,
                damage: hit.amount,
                hp_current: target.hp_current(),
                hp_max: target.hp_max(),
                damage_type: 0,
                is_critical: hit.is_critical as u8,
            })
        ));
        // Se o jogador toma dano, emitir S_STATUPDATE_HP
    }
}
```

### 2. Corrigir S_ATTACK_STATUS (0x05) em server.rs

```rust
pub struct HitPointOther {
    pub entity_id: u32,
    pub damage: i32,
    pub hp_current: u32,
    pub hp_max: u32,
    pub damage_type: u8,
    pub is_critical: u8,
}

impl Serialise for HitPointOther {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, HIT_POINT_OTHER, &mut ptr);
        to_le_bytes!(ptr, buf, self.entity_id);
        to_le_bytes!(ptr, buf, self.damage);
        to_le_bytes!(ptr, buf, self.hp_current);
        to_le_bytes!(ptr, buf, self.hp_max);
        buf[ptr] = self.damage_type; ptr += 1;
        buf[ptr] = self.is_critical; ptr += 1;
        prepend_length(buf, ptr)
    }
}
```

### 3. Adicionar S_STATUPDATE_HP (0x03) e S_STATUPDATE_MP (0x04) em server.rs

```rust
const HIT_POINT: u16 = 0x0003;
const HIT_POINT_MP: u16 = 0x0004;

pub struct HitPoint {
    pub hp_current: u32,
    pub hp_max: u32,
}
pub struct HitPointMp {
    pub mp_current: u32,
    pub mp_max: u32,
}
```

Emitir em `direct` (só para o jogador que tomou dano) quando NPC ataca o player.

### 4. Adicionar IA de ataque de NPC no update() tick (state.rs)

```rust
// Ciclo de aggro simples: NPC ataca o jogador mais próximo no raio de aggro
for entity in &mut self.entities {
    if entity.target().is_some() {
        if entity.next_attack <= Instant::now() {
            entity.next_attack = Instant::now() + Duration::from_millis(2000);
            // Calcular dano do NPC
            let damage = entity.base_attack();
            // Encontrar o client_id do jogador-alvo
            // Emitir S_STATUPDATE_HP para o jogador (direct)
            // Emitir S_ATTACK_STATUS para outros (broadcast)
        }
    }
}
```

### 5. Calcular e emitir S_STATUPDATE_DP (0x06) quando skill usa DP

```rust
const HIT_POINT_DP: u16 = 0x0006;
pub struct HitPointDp {
    pub dp_current: u32,
    pub dp_max: u32,
}
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Corrigir `HitPointOther`, adicionar `HitPoint` (0x03), `HitPointMp` (0x04), `HitPointDp` (0x06) |
| `game-server/src/game/state.rs` | Ciclo de auto-ataque com timer, IA básica de NPC |
| `game-server/src/game/engine/damage.rs` | Cálculo de critical hit baseado em stat CRIT do personagem |
| `game-server/src/game/character.rs` | Método `attack_speed_ms()` baseado em attack_speed stat |

---

## Verificação

- Atacar NPC → HP do NPC deve diminuir e S_ATTACK_STATUS chegar.
- Parar ataque (target_id=0) → timer deve ser removido.
- Critical hit deve aparecer na interface.
- NPC deve contra-atacar e reduzir HP do jogador (S_STATUPDATE_HP).

---

**Commit:** `git add -A && git commit -m "PLAN-04: Auto-ataque com timer de swing, S_ATTACK_STATUS corrigido, NPC aggro básico, S_STATUPDATE_HP/MP/DP"`
