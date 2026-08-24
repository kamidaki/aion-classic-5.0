# PLAN-02: Movimentação — C_MOVE (0x30), S_MOVE (0x37), Windstream (0x046/0x0a2/0x0a3)

**Status:** `[x]`  
**Prioridade:** ALTA — o personagem se move, mas Windstream e voo não funcionam.

---

## Contexto da Captura Wireshark

### Movimentação Normal
89 pacotes de Windstream + 1220 pacotes de movimento registrados na sessão.

**C_MOVE (CM, opcode 0x30) — estrutura wire atual no código:**
```
[u32 entity_id]
[f32 x][f32 y][f32 z]
[u8  heading]        — 0–120
[u8  move_type]      — 0=andar, 1=correr, 2=voar, 3=planar
[f32 speed_x]        — vx
[f32 speed_y]        — vy
[f32 speed_z]        — vz
```

**S_MOVE (SM, opcode 0x37) — precisa refletir para os outros jogadores:**
```
[u16 len]
[u16 opcode=0x0037]
[u8  SERVER_BYTE=0x65]
[u16 checksum=!opcode]
[u32 entity_id]
[f32 x][f32 y][f32 z]
[u8  heading]
[u8  move_type]
[f32 vx][f32 vy][f32 vz]
```

### Windstream (Correntes de Vento)

Opcodes capturados: `C_WIND_PATH` (0x046), `C_PATH_FLY` (0x031), `S_WIND_STATE_INFO` (0x0a3), `S_WIND_PATH_RESULT` (0x0a2).

**C_WIND_PATH (0x046) — cliente entra numa corrente de vento:**
```
[u32 windstream_id]   — ID da corrente de vento (do template do mapa)
[u8  action]          — 0x01=entrar, 0x02=sair
```

**S_WIND_STATE_INFO (0x0a3) — servidor confirma estado da corrente:**
```
[u32 entity_id]
[u32 windstream_id]
[u8  state]           — 0=fora, 1=dentro, 2=saindo
[f32 speed]           — velocidade da corrente (ex: 22.0)
```

**S_WIND_PATH_RESULT (0x0a2) — servidor envia rota pre-calculada:**
```
[u32 entity_id]
[u32 windstream_id]
[u16 waypoint_count]
-- para cada waypoint:
  [f32 x][f32 y][f32 z]  — 12 bytes por waypoint
[f32 duration_ms]         — tempo total em ms
```

**C_PATH_FLY (0x031) — cliente reporta progresso no voo:**
```
[u32 entity_id]
[u32 windstream_id]
[f32 x][f32 y][f32 z]
[f32 progress]           — 0.0 a 1.0
```

---

## Estado Atual do Código

**`game-server/src/game/message/client.rs`:** `MoveNew` (0x30) está implementado e faz broadcast via `S_MOVE`.  
**Problema 1:** O opcode do C_MOVE é 0x30 mas define_messages registra como `MOVE_NEW` — correto. O S_MOVE em `server.rs` existe como `MoveNew`. Verificar se o broadcast está chegando para outros jogadores (atualmente só 1 jogador, não testável isoladamente).

**Problema 2:** Windstream não tem handler. `C_WIND_PATH` (0x046) cai no `WARNING: Client Opcode not implemented`.

**`game-server/src/game/environment.rs`:** Tem `WindstreamState` mas não conectado ao handler de pacotes.

---

## Tarefas

### 1. Adicionar handler C_WIND_PATH (0x046) em client.rs

```rust
define_messages!(
    // ... existentes ...
    (WIND_PATH, WindPath, 0x46),
    (PATH_FLY, PathFly, 0x31),
);

#[derive(Debug, Clone)]
pub struct WindPath {
    pub windstream_id: u32,
    pub action: u8, // 1=entrar, 2=sair
}

impl WindPath {
    pub fn handle(&self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        // Emitir S_WIND_STATE_INFO confirmando entrada
        vec![s::Message::WindStateInfo(s::WindStateInfo {
            entity_id: session.character_id(),
            windstream_id: self.windstream_id,
            state: self.action,   // 1=dentro
            speed: 22.0,          // valor padrão; idealmente lido do template do mapa
        })]
    }
}

impl Deserialise for WindPath {
    fn deserialise(buf: &[u8]) -> Self {
        Self {
            windstream_id: u32::from_le_bytes(buf[0..4].try_into().unwrap()),
            action: buf[4],
        }
    }
}
```

### 2. Adicionar S_WIND_STATE_INFO (0x0a3) em server.rs

```rust
const WIND_STATE_INFO: u16 = 0x00A3;

pub struct WindStateInfo {
    pub entity_id: u32,
    pub windstream_id: u32,
    pub state: u8,
    pub speed: f32,
}

impl Serialise for WindStateInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(&mut buf[ptr..], WIND_STATE_INFO, &mut ptr);
        buf[ptr..ptr+4].copy_from_slice(&self.entity_id.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.windstream_id.to_le_bytes()); ptr += 4;
        buf[ptr] = self.state; ptr += 1;
        buf[ptr..ptr+4].copy_from_slice(&self.speed.to_le_bytes()); ptr += 4;
        prepend_length(buf, ptr)
    }
}
```

### 3. Adicionar S_WIND_PATH_RESULT (0x0a2) em server.rs

```rust
const WIND_PATH_RESULT: u16 = 0x00A2;

pub struct WindPathResult {
    pub entity_id: u32,
    pub windstream_id: u32,
    pub waypoints: Vec<(f32, f32, f32)>,
    pub duration_ms: f32,
}
```

### 4. Adicionar handler C_PATH_FLY (0x031) em client.rs

Apenas confirmar posição — não emite resposta, mas atualiza posição no State:
```rust
tx.send(ClientUpdate::new(session.client_id(), session.character_id(),
    Message::PathFly(PathFly { ... })));
```

### 5. Conectar environment.rs ao pipeline de pacotes

O `WindstreamService` em `environment.rs` deve ser consultado em `state.rs` para:
- Verificar se o windstream_id é válido no mapa atual.
- Retornar os waypoints pré-definidos do template.

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Adicionar `WindPath` (0x46) e `PathFly` (0x31) |
| `game-server/src/game/message/server.rs` | Adicionar `WindStateInfo` (0xA3) e `WindPathResult` (0xA2) |
| `game-server/src/game/environment.rs` | Expor `WindstreamService::get_waypoints(windstream_id)` |
| `game-server/src/game/state.rs` | Handler para `ClientUpdate::WindPath` no `respond()` |

---

## Verificação

- Entrar numa corrente de vento → personagem deve ser transportado ao longo da rota.
- C_PATH_FLY deve ser recebido e posição atualizada sem crash.
- S_WIND_STATE_INFO com state=0 deve ser enviado ao sair da corrente.

---

**Commit:** `git add -A && git commit -m "PLAN-02: Windstream C_WIND_PATH/S_WIND_STATE_INFO/S_WIND_PATH_RESULT implementados"`
