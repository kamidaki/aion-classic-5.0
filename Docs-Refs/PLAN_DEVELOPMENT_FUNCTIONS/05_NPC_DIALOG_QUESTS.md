# PLAN-05: NPC Dialog e Quests (SM_DIALOG_WINDOW 0x3C, CM_SHOW_DIALOG 0x34, SM_QUEST_LIST 0x47)

**Status:** `[x]`  
**Prioridade:** ALTA — missões são o loop principal do tutorial.

---

## Contexto da Captura Wireshark

A sessão registrou interação completa com NPCs de missão: aceitar missão, completar objetivos, entrega de recompensas (XP, Kinah, itens).

### C_SHOW_DIALOG (0x34) — cliente clica em NPC

```
[u32 npc_object_id]   — ID da entidade NPC na cena
[u32 dialog_id]       — 0 para abrir o dialog inicial
```

### C_DIALOG_SELECT (0x36) — jogador seleciona opção no dialog HTML

```
[u32 npc_object_id]
[u32 dialog_action]   — ID da ação (aceitar quest = 10003, completar = 10004, etc)
[u32 quest_id]        — 0 se não for quest-related
```

### SM_DIALOG_WINDOW (0x3C) — servidor abre janela HTML no cliente

```
[u32 npc_object_id]
[u32 dialog_id]       — identifica qual HTML o cliente renderiza
                        0 = saudação padrão
                        18 = lista de quests disponíveis
                        10 = seleção de teleport
                        2  = loja
[u32 quest_id]        — relevante quando dialog_id relacionado a quest
```

### SM_QUEST_LIST (0x47) — lista de missões ativas do personagem

```
[u16 quest_count]
-- para cada quest:
  [u32 quest_id]
  [u8  status]         — 0=ativa, 1=completa (aguardando entrega), 2=entregue
  [u32 flags]          — bitmask de objetivos completos
  [u32 vars[4]]        — variáveis de progresso (itens coletados, kills, etc)
  [u32 start_timestamp]
```

### S_QUEST_STARTED (SM, não capturado isoladamente — vem como code 0x47 atualizado)

Quando uma quest é aceita, o servidor re-envia SM_QUEST_LIST com a nova quest incluída.

---

## Estado Atual do Código

**`client.rs`:** `ShowDialog` (0x34) e `DialogSelect` (0x36) implementados.  
**`server.rs`:** `DialogWindow` (0x3C) implementado.  
**Problema crítico:** O `ShowDialog` não busca o NPC real — só retorna um dialog_id hardcoded. O `DialogSelect` não processa ações de quest (aceitar/completar). `SM_QUEST_LIST` (0x47) não está implementado (não existe em server.rs).

---

## Tarefas

### 1. Implementar SM_QUEST_LIST (0x47) em server.rs

```rust
const QUEST_LIST: u16 = 0x0047;

pub struct QuestEntry {
    pub quest_id: u32,
    pub status: u8,
    pub flags: u32,
    pub vars: [u32; 4],
    pub start_timestamp: u32,
}

pub struct QuestList {
    pub quests: Vec<QuestEntry>,
}

impl Serialise for QuestList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, QUEST_LIST, &mut ptr);
        to_le_bytes!(ptr, buf, self.quests.len() as u16);
        for q in &self.quests {
            to_le_bytes!(ptr, buf, q.quest_id);
            buf[ptr] = q.status; ptr += 1;
            to_le_bytes!(ptr, buf, q.flags);
            for v in &q.vars { to_le_bytes!(ptr, buf, v); }
            to_le_bytes!(ptr, buf, q.start_timestamp);
        }
        prepend_length(buf, ptr)
    }
}
```

### 2. Corrigir ShowDialog handler (state.rs)

Quando `C_SHOW_DIALOG` chega:
1. Buscar a entidade pelo `npc_object_id` em `self.entities`.
2. Consultar o template do NPC (`game_data.npcs.get(npc_id)`) para saber que dialogs ele oferece.
3. Retornar `SM_DIALOG_WINDOW` com o `dialog_id` correto:
   - NPC de missão → `dialog_id = 18` (lista de quests)
   - NPC de loja → `dialog_id = 2`
   - NPC de teleporte → `dialog_id = 10`

```rust
// Em state.rs respond():
ClientUpdate: ShowDialog { npc_object_id, dialog_id } => {
    if let Some(entity) = self.entities.iter().find(|e| e.id() == npc_object_id) {
        let npc_def = self.game_data.npcs.get(&entity.npc_id());
        let dialog = npc_def.map(|d| d.dialog_id).unwrap_or(0);
        messages.push_direct(update.client_id(), ServerUpdate::new(
            s::Message::DialogWindow(s::DialogWindow {
                npc_object_id,
                dialog_id: dialog,
                quest_id: 0,
            })
        ));
    }
}
```

### 3. Implementar DialogSelect para aceitar/completar quests

```rust
// dialog_action = 10003: aceitar quest
// dialog_action = 10004: completar quest (entregar)
ClientUpdate: DialogSelect { npc_object_id, dialog_action, quest_id } => {
    match dialog_action {
        10003 => {
            // Aceitar quest: adicionar ao character.active_quests
            let char = self.characters.get_mut(&update.character_id())?;
            char.start_quest(quest_id, current_timestamp());
            // Salvar no banco
            self.db.save_quest(char.id(), quest_id, 0, 0, [0;4]);
            // Emitir SM_QUEST_LIST atualizado
            messages.push_direct(update.client_id(), ServerUpdate::new(
                s::Message::QuestList(char.build_quest_list())
            ));
            // Fechar dialog
            messages.push_direct(update.client_id(), ServerUpdate::new(
                s::Message::DialogWindow(s::DialogWindow {
                    npc_object_id, dialog_id: 0, quest_id: 0
                })
            ));
        }
        10004 => {
            // Completar quest: dar recompensas, marcar como entregue
            let char = self.characters.get_mut(&update.character_id())?;
            if let Some(quest) = char.complete_quest(quest_id) {
                // Dar XP, Kinah, itens de recompensa
                char.add_exp(quest.exp_reward);
                char.add_kinah(quest.kinah_reward);
                // Emitir S_STATUPDATE_EXP (0x08), atualizar inventário
                messages.push_direct(update.client_id(), ServerUpdate::new(
                    s::Message::ExpUpdate(s::ExpUpdate::new(char.exp(), char.exp_required()))
                ));
            }
        }
        _ => {}
    }
}
```

### 4. Emitir SM_QUEST_LIST no spawn inicial

No fluxo de `C_LEVEL_READY`, após S_SKILL_LIST, emitir:
```rust
messages.push_direct(client_id, s::Message::QuestList(char.build_quest_list()));
```

### 5. Adicionar tabela `quests` no banco de dados

```sql
CREATE TABLE IF NOT EXISTS character_quests (
    character_id INTEGER NOT NULL,
    quest_id     INTEGER NOT NULL,
    status       INTEGER NOT NULL DEFAULT 0,  -- 0=ativa, 1=completa, 2=entregue
    flags        INTEGER NOT NULL DEFAULT 0,
    var1 INTEGER DEFAULT 0, var2 INTEGER DEFAULT 0,
    var3 INTEGER DEFAULT 0, var4 INTEGER DEFAULT 0,
    start_ts     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (character_id, quest_id),
    FOREIGN KEY (character_id) REFERENCES players(id)
);
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Adicionar `QuestList` (0x47), `ExpUpdate` (0x08) |
| `game-server/src/game/state.rs` | Handlers de `ShowDialog` e `DialogSelect` com lógica real de quest |
| `game-server/src/game/character.rs` | Métodos `start_quest()`, `complete_quest()`, `build_quest_list()` |
| `game-server/src/db.rs` | Operações CRUD para `character_quests` |
| `game-server/src/game/data/npc.rs` | Adicionar campo `dialog_id` no template NPC |

---

## Verificação

- Clicar em NPC de missão → janela de quest deve abrir.
- Aceitar quest → aparece na lista de missões ativas.
- Completar objetivos → flags atualizadas.
- Entregar quest → XP e Kinah adicionados, quest removida da lista ativa.

---

**Commit:** `git add -A && git commit -m "PLAN-05: SM_DIALOG_WINDOW real por tipo NPC, SM_QUEST_LIST implementado, aceitar/completar quests funcional"`
