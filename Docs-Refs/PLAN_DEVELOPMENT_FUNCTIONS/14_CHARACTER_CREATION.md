# PLAN-14: Criação de Personagem — CM_CREATE_CHARACTER Completo, Kit Inicial, Skills

**Status:** `[x]`  
**Prioridade:** ALTA — a criação de personagem é o ponto de entrada para qualquer jogador novo.

---

## Contexto da Captura Wireshark

A sessão capturou a criação de um assassino, um templário e um ranger. Os kits iniciais foram confirmados.

### CM_CREATE_CHARACTER (0x0C) — pacote do cliente

```
[u16 name_len]
[u8* name]              — UTF-16LE, max 16 chars (32 bytes)
[u32 race]              — 0=Elyos, 1=Asmodian
[u32 gender]            — 0=male, 1=female
[u32 class_id]          — ID da classe final (1=Battlemaster/Gladiator, 2=Knight, etc)
[u32 face_id]           — índice do rosto (0-based)
[u32 hair_id]           — índice do cabelo
[u32 voice_id]          — 0=voice_m_1, 1=voice_m_2, etc
[u32 skin_color]        — cor RGB em u32
[u32 hair_color]
[u32 lip_color]
[u32 eye_color]
-- slots de equipamento inicial (do kit da classe):
[u32 head_item_id]      — item_id do capacete/elmo
[u32 chest_item_id]
[u32 legs_item_id]
[u32 boots_item_id]
[u32 gloves_item_id]
[u32 weapon_item_id]
```

### SM_CREATE_CHARACTER (0x00C8) — resposta do servidor

```
[u8  result]    — 0=sucesso, 1=nome em uso, 2=nome inválido, 3=limite de personagens
[u32 char_id]   — ID do personagem criado (se result=0)
```

### Kit inicial por classe (confirmado na captura)

| Classe | Torso | Calças | Botas | Luvas | Arma |
|--------|-------|--------|-------|-------|------|
| BATTLEMASTER | lt_torso_n_l1_battlemaster_1a | lt_pants_n_l1_battlemaster_1a | lt_feet_n_l1_battlemaster_1a | lt_hands_n_l1_battlemaster_1a | sword_l1_1a |
| KNIGHT | hv_torso_n_l1_knight_1a | hv_pants_n_l1_knight_1a | hv_feet_n_l1_knight_1a | hv_hands_n_l1_knight_1a | sword_l1_1a |
| ASSASSIN | lt_torso_n_l1_assassin_1a | lt_pants_n_l1_assassin_1a | lt_feet_n_l1_assassin_1a | lt_hands_n_l1_assassin_1a | dagger_l1_1a |
| RANGER | lt_torso_n_l1_ranger_1a | lt_pants_n_l1_ranger_1a | lt_feet_n_l1_ranger_1a | lt_hands_n_l1_ranger_1a | bow_l1_1a |
| WIZARD | cl_torso_n_l1_mage_1a | cl_pants_n_l1_mage_1a | cl_feet_n_l1_mage_1a | cl_hands_n_l1_mage_1a | staff_l1_1a |
| ELEMENTALLIST | cl_torso_n_l1_mage_1a | cl_pants_n_l1_mage_1a | cl_feet_n_l1_mage_1a | cl_hands_n_l1_mage_1a | staff_l1_1a |
| CLERIC | cl_torso_n_l1_cleric_1a | cl_pants_n_l1_cleric_1a | cl_feet_n_l1_cleric_1a | cl_hands_n_l1_cleric_1a | mace_l1_1a |
| CHANTER | cl_torso_n_l1_chanter_1a | cl_pants_n_l1_chanter_1a | cl_feet_n_l1_chanter_1a | cl_hands_n_l1_chanter_1a | staff_l1_1a |

---

## Estado Atual do Código

**`client.rs`:** `CreateCharacter` (0x5F) implementado — delega para state via tx.  
**`state.rs`:** Handler de `CreateCharacter` presente — cria personagem no banco.  
**Problema:** A criação não insere o kit inicial de equipamentos no inventário. Não calcula HP/MP base para a classe/nível 1. Não grava as skills iniciais. Não define spawn point correto.

---

## Tarefas

### 1. Completar parsing de CM_CREATE_CHARACTER

```rust
#[derive(Debug, Clone)]
pub struct CreateCharacter {
    pub name: String,
    pub race: u32,
    pub gender: u32,
    pub class_id: u32,
    pub face_id: u32,
    pub hair_id: u32,
    pub voice_id: u32,
    pub skin_color: u32,
    pub hair_color: u32,
    pub lip_color: u32,
    pub eye_color: u32,
    // Itens do kit (para validação, não confiar cegamente no cliente)
    pub head_item: u32,
    pub chest_item: u32,
    pub legs_item: u32,
    pub boots_item: u32,
    pub gloves_item: u32,
    pub weapon_item: u32,
}
```

### 2. Implementar criação completa no state.rs

```rust
fn create_character(&self, msg: &c::CreateCharacter, account_name: &str) -> Result<u32, u8> {
    // 1. Validar nome
    if !is_valid_name(&msg.name) { return Err(2); }
    if self.db.name_exists(&msg.name) { return Err(1); }
    if self.db.count_chars(account_name) >= 8 { return Err(3); }
    
    // 2. Stats base por classe/nível 1
    let (base_hp, base_mp) = base_stats_for_class(msg.class_id, 1);
    
    // 3. Coordenadas iniciais por raça
    let (map_id, x, y, z) = match msg.race {
        0 => (110070000u32, 457.0f32, 251.0f32, 127.04f32), // Elyos - Kaisinel
        1 => (120070000u32, 457.0f32, 251.0f32, 127.04f32), // Asmodian
        _ => return Err(3),
    };
    
    // 4. Criar personagem no banco
    let char_id = self.db.create_character(CharacterData {
        account_name: account_name.to_string(),
        name: msg.name.clone(),
        race: msg.race as u8,
        gender: msg.gender as u8,
        class_id: msg.class_id as u8,
        level: 1,
        exp: 0,
        hp_current: base_hp,
        mp_current: base_mp,
        map_id, x, y, z,
        heading: 0,
        appearance: serde_json::json!({
            "face": msg.face_id,
            "hair": msg.hair_id,
            "voice": msg.voice_id,
            "skin_color": msg.skin_color,
            "hair_color": msg.hair_color,
        }).to_string(),
    })?;
    
    // 5. Adicionar kit inicial ao inventário
    let kit = kit_for_class(msg.class_id);
    for item_template_id in kit {
        self.db.add_item(char_id, item_template_id, 1)?;
    }
    
    // 6. Adicionar skills iniciais
    let skills = initial_skills_for_class(msg.class_id, &self.game_data);
    self.db.save_skills(char_id, &skills)?;
    
    Ok(char_id)
}
```

### 3. Definir kits iniciais por classe (state.rs ou data/gear.rs)

```rust
fn kit_for_class(class_id: u32) -> Vec<u32> {
    // IDs retirados do client XML — verificar em items.xml do cliente
    match class_id {
        1 => vec![ // BATTLEMASTER
            186000001, // sword_l1_1a
            110300001, // lt_torso_n_l1_battlemaster_1a
            110700001, // lt_pants_n_l1_battlemaster_1a
            111100001, // lt_feet_n_l1_battlemaster_1a
            111500001, // lt_hands_n_l1_battlemaster_1a
        ],
        2 => vec![ // KNIGHT
            186000001, // sword_l1_1a
            120300001, // hv_torso_n_l1_knight_1a
            // ...
        ],
        // ... demais classes
        _ => vec![],
    }
}
```

> **NOTA:** Os item_template_ids exatos devem ser extraídos do arquivo `items.xml` do cliente Aion. Usar os nomes de catálogo confirmados na captura como referência.

### 4. Calcular HP/MP base por classe e nível

```rust
fn base_stats_for_class(class_id: u32, level: u8) -> (u32, u32) {
    // Valores base do nível 1 — extraídos do player_stats.xml do cliente
    match class_id {
        1 | 2 => (1278, 577), // Fighter classes
        3 | 4 | 5 => (1148, 634), // Scout classes
        6 | 7 | 8 => (976, 1022), // Mage classes
        9 | 10 | 11 => (1050, 908), // Priest classes
        _ => (1000, 500),
    }
}
```

### 5. Skills iniciais por classe

```rust
fn initial_skills_for_class(class_id: u32, game_data: &GameData) -> Vec<Skill> {
    // Usar game_data.skills e filtrar por classe
    // Fonte: client_skill_learns.xml — skills de nível 0 e 1 da classe
    // Confirmado: um feiticeiro (class 7) nível 11 tem 29 skills
    // Classes base: FIGHTER, SCOUT, MAGE, PRIEST recebem skills universais
    let (class_name, base_class) = classe_no_xml(class_id);
    game_data.skills.iter()
        .filter(|s| s.class == class_name || s.class == base_class || s.class == "UNIVERSAL")
        .filter(|s| s.min_level <= 1)
        .cloned()
        .collect()
}
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Completar parsing de `CreateCharacter` (0x5F) com todos os campos |
| `game-server/src/game/message/server.rs` | Verificar `CreateCharacter` response (0xC8) — campos corretos |
| `game-server/src/game/state.rs` | `create_character()` completo com kit, skills, coords |
| `game-server/src/game/data/gear.rs` | `kit_for_class()` com item IDs reais |
| `game-server/src/game/state.rs` | `base_stats_for_class()` e `initial_skills_for_class()` |
| `game-server/src/db.rs` | `create_character()` com novo schema (PLAN-13) |

---

## Verificação

- Criar personagem → aparece na tela de seleção.
- Entrar no mundo → spawn no local correto com kit equipado.
- Skills visíveis na barra de ação.
- HP/MP corretos para nível 1 da classe.
- Nome duplicado → erro correto (result=1).

---

**Commit:** `git add -A && git commit -m "PLAN-14: Criação de personagem completa — kit inicial por classe, skills L1, HP/MP base, spawn Kaisinel/Asmodae"`
