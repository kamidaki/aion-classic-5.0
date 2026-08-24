# PLAN-15: Teleporte de Mundo — S_REQUEST_TELEPORT Wire, Troca de Mapa, Instâncias

**Status:** `[ ]`  
**Prioridade:** ALTA — troca de mapa via NPC teleportador é funcionalidade central.

---

## Contexto da Captura Wireshark

5 teleportes capturados. Estrutura do S_REQUEST_TELEPORT decodificada com certeza:

```
S_REQUEST_TELEPORT (opcode 0x014):
Wire total (com framing): 27 bytes
  [u16 len=0x001B]         — 27 bytes total
  [u16 opcode=0x0014]
  [u8  SERVER_BYTE=0x65]
  [u16 checksum=!0x0014]
  [u8  tipo]               — 0=portal NPC, 1=zona, 2=instância, 3=bindstone
  [u32 map_id]             — ID do mapa destino
  [u32 instance_id]        — 0 para mundo aberto
  [f32 X]
  [f32 Y]
  [f32 Z]
  [u8  heading]
Total payload: 22 bytes = 1 + 4 + 4 + 4 + 4 + 4 + 1
```

**Teleportes capturados (valores reais do servidor oficial):**

| # | tipo | map_id | instance_id | X | Y | Z | heading |
|---|------|--------|-------------|---|---|---|---------|
| 1 | 0x00 | 110070000 | 0 | 457.00 | 251.00 | 127.04 | 0 |
| 2 | 0x00 | 110010000 | 0 | 1352.14 | 1514.12 | 569.04 | 90 |
| 3 | 0x00 | 110010000 | 0 | 1352.14 | 1514.12 | 569.04 | 90 |
| 4 | 0x00 | 120010000 | 0 | 1649.59 | 1399.40 | 194.40 | 0 |
| 5 | 0x00 | 120010000 | 0 | 1649.59 | 1399.40 | 194.40 | 0 |

**S_WORLD_SCENE_STATUS (0x08B) — antes do teleporte:**
```
[u32 scene_id]    — 0=nenhuma cena, outros IDs para cutscenes específicas
[u8  status]      — 1=iniciar cena, 0=encerrar
```

---

## Estado Atual do Código

**`server.rs`:** `WorldSceneStatus` (0x08B) presente.  
**`teleport.rs`:** `TeleportService` tem localizações hardcoded mas não emite `S_REQUEST_TELEPORT`.  
**Problema crítico:** O fluxo de teleporte não está conectado. Quando o jogador clica num NPC de teleporte:
1. `C_SHOW_DIALOG` abre dialog de teleporte.
2. `C_DIALOG_SELECT` seleciona destino.
3. O servidor deve emitir `S_REQUEST_TELEPORT` para o cliente.
4. O cliente inicia carregamento do mapa.
5. O cliente reconecta (mesmo socket) e envia `C_ENTER_WORLD` ou similar para confirmar chegada.

**Passo 5 não está claro** — precisa verificar na captura se o cliente mantém a conexão TCP ou abre uma nova para o mapa destino.

---

## Tarefas

### 1. Verificar fluxo pós-teleporte na captura

Analisar os pacotes do Wireshark após cada S_REQUEST_TELEPORT:
- O cliente manda algum C_* confirmando chegada no novo mapa?
- O servidor manda S_WORLD? S_STATUS? Burst de NPCs?
- A sequência é a mesma do login inicial?

**Sequência esperada após S_REQUEST_TELEPORT (baseado em outros emuladores Java):**
1. S_REQUEST_TELEPORT → cliente inicia carregamento
2. Cliente manda C_LEVEL_READY (0x19) ao terminar de carregar
3. Servidor manda burst: S_STATS_INFO + NPCs em cena + S_SKILL_LIST

### 2. Emitir S_REQUEST_TELEPORT a partir do DialogSelect

```rust
// Em state.rs, handler de DialogSelect para teleporte:
c::Message::DialogSelect(msg) if msg.dialog_action == TELEPORT_ACTION => {
    let char = self.characters.get_mut(&update.character_id())?;
    
    // Consultar TeleportService
    if let Ok((loc, remaining_kinah)) = self.teleport_service.validate_and_teleport(
        msg.teleport_loc_id,
        char.level(),
        char.race(),
        char.kinah(),
    ) {
        // Cobrar kinah
        char.remove_kinah(remaining_kinah);
        
        // Emitir S_REQUEST_TELEPORT
        messages.push_direct(update.client_id(), ServerUpdate::new(
            s::Message::RequestTeleport(s::RequestTeleport {
                tipo: 0x00,
                map_id: loc.map_id,
                instance_id: 0,
                x: loc.x,
                y: loc.y,
                z: loc.z,
                heading: loc.heading,
            })
        ));
        
        // Fechar dialog
        messages.push_direct(update.client_id(), ServerUpdate::new(
            s::Message::DialogWindow(s::DialogWindow { npc_object_id: msg.npc_object_id, dialog_id: 0, quest_id: 0 })
        ));
        
        // Atualizar posição do personagem no State
        char.set_location(loc.map_id, loc.x, loc.y, loc.z, loc.heading);
    }
}
```

### 3. Adicionar S_REQUEST_TELEPORT (0x014) em server.rs

```rust
const REQUEST_TELEPORT: u16 = 0x0014;

pub struct RequestTeleport {
    pub tipo: u8,
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
        // Header (5 bytes: opcode u16 + SERVER_BYTE u8 + checksum u16)
        let opcode: u16 = REQUEST_TELEPORT;
        buf[ptr..ptr+2].copy_from_slice(&encrypt_server_opcode(opcode).to_le_bytes()); ptr += 2;
        buf[ptr] = SERVER_BYTE; ptr += 1;
        buf[ptr..ptr+2].copy_from_slice(&(!opcode).to_le_bytes()); ptr += 2;
        // Payload: 22 bytes
        buf[ptr] = self.tipo; ptr += 1;
        buf[ptr..ptr+4].copy_from_slice(&self.map_id.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.instance_id.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.x.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.y.to_le_bytes()); ptr += 4;
        buf[ptr..ptr+4].copy_from_slice(&self.z.to_le_bytes()); ptr += 4;
        buf[ptr] = self.heading; ptr += 1;
        // Prepend length: total = ptr + 2
        let total = ptr + 2;
        let len_bytes = (total as u16).to_le_bytes();
        // Shift buffer to make room for length
        buf.copy_within(0..ptr, 2);
        buf[0..2].copy_from_slice(&len_bytes);
        ptr + 2  // total length
    }
}
```

### 4. Expandir TeleportService com locais reais da captura

```rust
impl TeleportService {
    pub fn new() -> Self {
        let mut locs = HashMap::new();
        
        // Sanctum — coordenadas exatas da captura
        locs.insert(100001, TeleportLocation {
            loc_id: 100001, map_id: 110010000,
            x: 1352.14, y: 1514.12, z: 569.04, heading: 90,
            price: 0, required_level: 1, required_race: Some(0),
        });
        
        // Pandaemonium — coordenadas exatas da captura
        locs.insert(200001, TeleportLocation {
            loc_id: 200001, map_id: 120010000,
            x: 1649.59, y: 1399.40, z: 194.40, heading: 0,
            price: 0, required_level: 1, required_race: Some(1),
        });
        
        // Adicionar todos os locais de teleporte padrão da versão 4.5
        // (extrair da tabela teleporter_templates do emulador Java de referência)
        
        Self { locations: locs }
    }
}
```

### 5. Limpar NPCs em cena do mapa anterior

Quando S_REQUEST_TELEPORT é emitido, limpar `npcs_em_cena[char_id]` no State para que o novo mapa carregue do zero:

```rust
self.npcs_em_cena.remove(&update.character_id());
self.mundo_enviado.remove(&update.character_id());
```

### 6. Troca de mapa via SM_DIALOG_WINDOW teleporte

O dialog_id para teleporte é `10`. O payload do `SM_DIALOG_WINDOW` deve incluir a lista de destinos disponíveis. Verificar na captura o formato exato — pode ser que o cliente renderize o HTML a partir de um template fixo, apenas necessitando do `dialog_id=10`.

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Adicionar `RequestTeleport` (0x014) com estrutura correta de 22 bytes |
| `game-server/src/game/state.rs` | Conectar DialogSelect → teleporte → emitir S_REQUEST_TELEPORT |
| `game-server/src/game/teleport.rs` | Expandir locais com coordenadas reais da captura |
| `game-server/src/game/state.rs` | Limpar npcs_em_cena e mundo_enviado ao teleportar |
| `game-server/src/game/character.rs` | `set_location()` atualiza map_id, x, y, z, heading |

---

## Verificação

- Clicar em NPC de teleporte → dialog_id=10 abre lista de destinos.
- Selecionar Sanctum → S_REQUEST_TELEPORT { map_id: 110010000, x: 1352.14, ... }.
- Mapa carrega → burst de NPCs do Sanctum em cena.
- Clicar em NPC de teleporte de Sanctum → pode voltar a Kaisinel Academy.
- Mapa antigo não tem NPCs fantasmas (npcs_em_cena limpo).

---

**Commit:** `git add -A && git commit -m "PLAN-15: Teleporte completo — S_REQUEST_TELEPORT 22-byte fiel à captura, DialogSelect conectado, limpeza de cena ao trocar mapa"`
