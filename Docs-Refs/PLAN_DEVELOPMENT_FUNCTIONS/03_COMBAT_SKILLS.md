# PLAN-03: Combate — Skills (C_USE_SKILL 0x021, S_SKILL_SUCCEDED 0x02B, S_ABNORMAL_STATUS 0x031/0x032)

**Status:** `[x]`  
**Prioridade:** ALTA — 311 pacotes de skill capturados, incluindo 3 categorias distintas.

---

## Contexto da Captura Wireshark

**311 pacotes** capturados: alvo único (targeted), buff próprio (self-buff) e área (AoE).

### C_USE_SKILL (0x021) — cliente usa uma skill

```
[u32 skill_id]      — ID da skill (do skill_learn do XML)
[u32 target_id]     — 0 se self-buff ou AoE sem alvo
[u8  skill_level]   — nível da skill (1–15 geralmente)
[u8  cast_type]     — 0=instant, 1=cast_time, 2=channeling
[f32 x][f32 y][f32 z]  — posição do caster ao usar
[u8  heading]
```

### S_SKILL_SUCCEDED (0x02B) — servidor confirma execução

```
[u32 caster_id]
[u32 target_id]
[u32 skill_id]
[u8  skill_level]
[u32 effect_count]
-- para cada efeito:
  [u32 target_id]
  [i32 damage]      — negativo = dano, positivo = cura
  [u8  damage_type] — 0=físico, 1=mágico, 2=true
  [u8  is_critical] — 0 ou 1
```

### S_SKILL_PENALTY_STATUS_OTHER (0x0d8) — penalidade de skill (cooldown broadcast)

```
[u32 entity_id]
[u32 skill_id]
[u32 cooldown_ms]
```

### S_ABNORMAL_STATUS (0x031) — buffs/debuffs no jogador LOCAL

```
[u32 entity_id]
[u32 effect_count]
-- para cada efeito ativo:
  [u32 skill_id]     — skill que aplicou o efeito
  [u32 remaining_ms] — tempo restante em ms
  [u8  stack]        — nível de stack (geralmente 1)
```

### S_ABNORMAL_STATUS_OTHER (0x032) — buffs/debuffs em OUTROS

Mesma estrutura do 0x031, mas para entity_id != player.

---

## Estado Atual do Código

**`client.rs`:** `UseSkill` (0x21) implementado — lê skill_id, target_id.  
**`server.rs`:** `UseSkill` (0x21) e `SkillSucceded` (0x2B) presentes.  
**Problema:** `UseSkill` serializa mas não inclui `effect_count` e loop de efeitos — o payload está incompleto. `S_ABNORMAL_STATUS` (0x31) e `S_ABNORMAL_STATUS_OTHER` (0x32) existem em server.rs mas sem os campos `remaining_ms` e `stack` por efeito.

---

## Tarefas

### 1. Corrigir S_SKILL_SUCCEDED (0x02B) em server.rs

Adicionar loop de efeitos com campo `damage_type` e `is_critical`:

```rust
pub struct SkillSucceded {
    pub caster_id: u32,
    pub target_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub effects: Vec<SkillEffect>,
}

pub struct SkillEffect {
    pub target_id: u32,
    pub damage: i32,     // negativo = dano, positivo = cura
    pub damage_type: u8, // 0=físico, 1=mágico, 2=true
    pub is_critical: u8,
}

impl Serialise for SkillSucceded {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, SKILL_SUCCEDED, &mut ptr);
        to_le_bytes!(ptr, buf, self.caster_id);
        to_le_bytes!(ptr, buf, self.target_id);
        to_le_bytes!(ptr, buf, self.skill_id);
        buf[ptr] = self.skill_level; ptr += 1;
        to_le_bytes!(ptr, buf, self.effects.len() as u32);
        for eff in &self.effects {
            to_le_bytes!(ptr, buf, eff.target_id);
            to_le_bytes!(ptr, buf, eff.damage);
            buf[ptr] = eff.damage_type; ptr += 1;
            buf[ptr] = eff.is_critical; ptr += 1;
        }
        prepend_length(buf, ptr)
    }
}
```

### 2. Corrigir S_ABNORMAL_STATUS (0x031) e S_ABNORMAL_STATUS_OTHER (0x032)

```rust
pub struct AbnormalStatus {
    pub entity_id: u32,
    pub effects: Vec<AbnormalEffect>,
}

pub struct AbnormalEffect {
    pub skill_id: u32,
    pub remaining_ms: u32,
    pub stack: u8,
}

impl Serialise for AbnormalStatus {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, ABNORMAL_STATUS, &mut ptr);
        to_le_bytes!(ptr, buf, self.entity_id);
        to_le_bytes!(ptr, buf, self.effects.len() as u32);
        for eff in &self.effects {
            to_le_bytes!(ptr, buf, eff.skill_id);
            to_le_bytes!(ptr, buf, eff.remaining_ms);
            buf[ptr] = eff.stack; ptr += 1;
        }
        prepend_length(buf, ptr)
    }
}
```

### 3. Adicionar S_SKILL_PENALTY_STATUS_OTHER (0x0D8) em server.rs

```rust
const SKILL_PENALTY_STATUS_OTHER: u16 = 0x00D8;

pub struct SkillPenaltyStatusOther {
    pub entity_id: u32,
    pub skill_id: u32,
    pub cooldown_ms: u32,
}
```

### 4. Integrar no state.rs — respond() para C_USE_SKILL

Quando `c::Message::UseSkill(msg)` chega:
1. Buscar character pelo `client_id`.
2. Calcular dano usando `engine::damage::Hit`.
3. Aplicar dano ao target (entity ou character).
4. Emitir `S_SKILL_SUCCEDED` (direct ao caster + broadcast para quem está em cena).
5. Emitir `S_ABNORMAL_STATUS_OTHER` para broadcast dos efeitos.
6. Emitir `S_SKILL_PENALTY_STATUS_OTHER` para cooldown broadcast.
7. Emitir `S_ATTACK_STATUS` (0x05) para atualizar HP do target no cliente.

### 5. Emitir S_SKILL_LIST (0x02C) no spawn

Após `C_LEVEL_READY`, emitir `S_SKILL_LIST` com as skills da classe do personagem.
Fonte das skills: `game-server/src/game/data/skill.rs` + `game_data.skills`.

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Corrigir `SkillSucceded`, `AbnormalStatus`, adicionar `SkillPenaltyStatusOther` |
| `game-server/src/game/message/client.rs` | Verificar/corrigir parse de `UseSkill` (cast_type, coordenadas) |
| `game-server/src/game/state.rs` | Handler completo de UseSkill no `respond()` |
| `game-server/src/game/engine/damage.rs` | Confirmar fórmulas físico/mágico fiel ao oficial |

---

## Verificação

- Usar skill de alvo único → S_SKILL_SUCCEDED deve chegar com dano correto.
- Usar self-buff → S_ABNORMAL_STATUS deve adicionar o efeito com tempo.
- Usar AoE → múltiplos targets devem receber dano no mesmo S_SKILL_SUCCEDED.
- Cooldown deve aparecer na barra de skills após uso.

---

**Commit:** `git add -A && git commit -m "PLAN-03: Skills completas — S_SKILL_SUCCEDED com efeitos, S_ABNORMAL_STATUS com remaining_ms, S_SKILL_PENALTY_STATUS_OTHER"`
