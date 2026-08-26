# Plano de Jogo - Camada DAO & Persistência SQLite

Este documento detalha o mapeamento da camada de acesso a dados (DAO) em Rust (migração de `com/aionemu/gameserver/dao/` do Java 4.8 para Rust com Rusqlite), cobrindo as **86 tabelas** distribuídas entre `login.db`, `game.db` e `chat.db`.

---

## 1. Mapeamento de DAOs Java 4.8 $\rightarrow$ Rust

| DAO Java 4.8 | Módulo em Rust | Tabelas SQLite Mapeadas |
| :--- | :--- | :--- |
| `dao.PlayerDAO` | `dao::player_dao.rs` | `characters`, `player_appearance`, `player_life_stats` |
| `dao.InventoryDAO` | `dao::inventory_dao.rs` | `inventory`, `item_cooldowns`, `item_stones` |
| `dao.PlayerSkillsDAO` | `dao::skill_dao.rs` | `player_skills`, `player_skill_cooldowns` |
| `dao.PlayerQuestsDAO` | `dao::quest_dao.rs` | `player_quests`, `player_quest_vars` |
| `dao.AbyssRankDAO` | `dao::abyss_dao.rs` | `abyss_rank`, `player_pvp_stats` |
| `dao.LegionDAO` | `dao::legion_dao.rs` | `legions`, `legion_members`, `legion_history`, `legion_announcements` |
| `dao.MailDAO` | `dao::mail_dao.rs` | `mail`, `mail_attachments` |
| `dao.BrokerDAO` | `dao::broker_dao.rs` | `broker`, `broker_history` |
| `dao.PlayerTitlesDAO` | `dao::title_dao.rs` | `player_titles` |
| `dao.FriendListDAO` | `dao::friend_dao.rs` | `friends`, `block_list` |
| `dao.SiegeDAO` | `dao::siege_dao.rs` | `siege_locations`, `siege_log` |
| `dao.SurveyDAO` | `dao::survey_dao.rs` | `surveys`, `survey_players` |
| `dao.BattlePassDAO` | `dao::battlepass_dao.rs`| `battlepass_season`, `battlepass_progress`, `battlepass_rewards` |

---

## 2. Transações Atômicas e Segurança em Rust

Para prevenir duplicação de itens (dupe bugs) e corrupção de saldo, todas as operações que envolvem transferência de Kinah ou itens usam transações atômicas `conn.transaction()`:

```rust
pub fn transfer_item_between_inventories(
    conn: &mut Connection,
    sender_id: u32,
    receiver_id: u32,
    item_obj_id: u32,
    quantity: u32,
) -> rusqlite::Result<()> {
    let tx = conn.transaction()?;
    
    // 1. Remove da bolsa do remetente
    tx.execute(
        "UPDATE inventory SET quantity = quantity - ?1 WHERE item_unique_id = ?2 AND item_owner = ?3",
        params![quantity, item_obj_id, sender_id],
    )?;
    
    // 2. Insere na bolsa do destinatário
    tx.execute(
        "INSERT INTO inventory(item_owner, item_id, quantity, slot) VALUES (?1, (SELECT item_id FROM inventory WHERE item_unique_id = ?2), ?3, ?4)",
        params![receiver_id, item_obj_id, quantity, 0],
    )?;
    
    tx.commit()
}
```

---

## 3. Otimizações de Alta Performance do SQLite

* **Modo WAL (Write-Ahead Logging)**: Ativado em todos os bancos (`PRAGMA journal_mode = WAL;`). Permite que leituras ocorram em paralelo absoluto com escritas sem nenhum travamento de lock.
* **Modo Síncrono Normal**: `PRAGMA synchronous = NORMAL;` para escrita rápida e sem gargalo de I/O em disco.
* **Prepared Statements em Cache**: Queries frequentes (como consulta de coordenadas e atualização de vida) são pré-compiladas na inicialização.
