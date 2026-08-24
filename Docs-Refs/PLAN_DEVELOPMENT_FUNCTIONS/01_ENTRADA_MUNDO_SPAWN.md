# PLAN-01: Entrada no Mundo — Spawn Inicial, Cutscene e S_REQUEST_TELEPORT

**Status:** `[x]`  
**Prioridade:** CRÍTICA — sem isso o personagem não entra no mundo corretamente.

---

## Contexto da Captura Wireshark

A sessão capturada registrou 5 teleportes. A estrutura do `S_REQUEST_TELEPORT` foi decifrada:

```
S_REQUEST_TELEPORT (opcode 0x014, 22 bytes de payload):
  [u8  tipo]         — 0x00=portal NPC, 0x01=zona, 0x02=instância
  [u32 map_id]       — ex.: 110070000 (Kaisinel Academy)
  [u32 instance_id]  — ex.: 0 (mundo aberto)
  [f32 X]            — ex.: 457.0
  [f32 Y]            — ex.: 251.0
  [f32 Z]            — ex.: 127.04
  [u8  heading]      — direção do personagem ao chegar (0–120)
```

**Coordenadas reais capturadas:**
| Teleporte | map_id | X | Y | Z |
|-----------|--------|---|---|---|
| #1 Kaisinel Academy (tutorial) | 110070000 | 457.0 | 251.0 | 127.04 |
| #2 Sanctum | 110010000 | 1352.14 | 1514.12 | 569.04 |
| #3 Sanctum | 110010000 | 1352.14 | 1514.12 | 569.04 |
| #4 Pandaemonium | 120010000 | 1649.59 | 1399.40 | 194.40 |
| #5 Pandaemonium | 120010000 | 1649.59 | 1399.40 | 194.40 |

**Sequência de pacotes do spawn inicial (ordem exata da captura):**
1. `S_ENTER_WORLD_CHECK` (0x00D) — permissão para carregar tela
2. `S_WORLD_SCENE_STATUS` (0x08B) — status da cena/cutscene do tutorial
3. `S_REQUEST_TELEPORT` (0x014) — posicionamento inicial no Kaisinel
4. Burst de NPCs em cena (S_NPC_INFO em loop)
5. `S_STATS_INFO` (0x001) — atributos do personagem
6. `S_SKILL_LIST` (0x02C) — skills da classe

---

## Estado Atual do Código

**Arquivo principal:** `game-server/src/game/message/server.rs`  
**Problema:** O `S_REQUEST_TELEPORT` está mapeado como `TeleportRequest` mas serializa campo `tipo` com tamanho errado (falta o byte de heading ao final). O `S_WORLD_SCENE_STATUS` (0x08B) é enviado mas sem o campo de cutscene correto.

**`game-server/src/game/teleport.rs`:** Estrutura presente mas `validate_and_teleport` só valida — não emite o pacote de teleporte real.

---

## Tarefas

### 1. Corrigir `S_REQUEST_TELEPORT` (server.rs)

```rust
// Estrutura correta — 22 bytes de payload + 2 len + 3 header = 27 wire bytes
pub struct RequestTeleport {
    pub tipo: u8,        // 0=portal, 1=zona, 2=instância
    pub map_id: u32,
    pub instance_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
}

impl Serialise for RequestTeleport {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        // header: opcode 0x0014 (2 bytes LE), SERVER_BYTE (1 byte), checksum (!opcode, 2 bytes)
        let opcode: u16 = 0x0014;
        buf[ptr..ptr+2].copy_from_slice(&opcode.to_le_bytes()); ptr += 2;
        buf[ptr] = SERVER_BYTE; ptr += 1;
        buf[ptr..ptr+2].copy_from_slice(&(!opcode).to_le_bytes()); ptr += 2;
        // payload
        buf[ptr] = self.tipo; ptr += 1;
        buf[ptr..ptr+4].copy_from_slice(&self.map_id.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.instance_id.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.x.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.y.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.z.to_le_bytes()); ptr += 4;
        buf[ptr] = self.heading; ptr += 1;
        // prepend length (u16 LE = total bytes)
        let total = ptr;
        let mut frame = vec![0u8; total + 2];
        frame[0..2].copy_from_slice(&(total as u16 + 2).to_le_bytes());
        frame[2..total+2].copy_from_slice(&buf[..total]);
        buf[..total+2].copy_from_slice(&frame);
        total + 2
    }
}
```

### 2. Emitir S_WORLD_SCENE_STATUS no fluxo correto (state.rs)

No handler de `C_LEVEL_READY` (opcode 0x19):
```rust
// Após o client enviar C_LEVEL_READY, o servidor responde:
// 1. S_WORLD_SCENE_STATUS { scene_id: 0, status: 1 } // liga a cena
// 2. S_REQUEST_TELEPORT com coordenadas do personagem
// 3. Burst de NPCs em cena (raio de visão)
// 4. S_STATS_INFO
// 5. S_SKILL_LIST
```

### 3. Corrigir coordenada inicial do personagem novo

Personagem recém-criado (Elyos) → Kaisinel Academy:
- map_id: 110070000, X: 457.0, Y: 251.0, Z: 127.04, heading: 0

Personagem recém-criado (Asmodian) → Asmodae intro zone:
- map_id: 120070000, X: 457.0, Y: 251.0, Z: 127.04, heading: 0

### 4. Verificação do S_ENTER_WORLD_CHECK (0x00D)

Deve ser enviado **antes** de S_WORLD_SCENE_STATUS. O campo `check_type`:
- `0x00`: entrada normal
- `0x01`: retorno de dungeon

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Corrigir `RequestTeleport::serialise()` — adicionar campo `heading` |
| `game-server/src/game/state.rs` | Handler de `C_LEVEL_READY`: emitir sequência correta de spawn |
| `game-server/src/game/teleport.rs` | Exportar coordenadas de spawn inicial por raça |
| `game-server/src/game/character.rs` | Adicionar campo `spawn_map_id` e `spawn_x/y/z` persistidos |

---

## Verificação

- Criar personagem novo → deve entrar em Kaisinel Academy nas coordenadas corretas.
- Personagem existente → deve aparecer nas coordenadas salvas no banco.
- S_WORLD_SCENE_STATUS deve disparar a cutscene do tutorial apenas para personagens novos.

---

**Commit:** `git add -A && git commit -m "PLAN-01: S_REQUEST_TELEPORT 22-byte fix, spawn inicial Kaisinel/Asmodae, fluxo C_LEVEL_READY"`
