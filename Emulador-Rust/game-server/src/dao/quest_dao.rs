use rusqlite::{params, Connection, Result};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuestPersistida {
    pub quest_id: u32,
    pub status: String,
    pub quest_vars: u32,
    pub complete_count: u32,
}

pub struct QuestDao;

impl QuestDao {
    /// Salva ou atualiza o estado de uma missão do personagem
    pub fn salvar_quest(
        conn: &Connection,
        character_id: u32,
        quest_id: u32,
        status: &str,
        quest_vars: u32,
        complete_count: u32,
    ) -> Result<()> {
        conn.execute(
            "INSERT INTO player_quests (character_id, quest_id, status, quest_vars, complete_count)
             VALUES (?1, ?2, ?3, ?4, ?5)
             ON CONFLICT(character_id, quest_id) DO UPDATE SET
             status = excluded.status, quest_vars = excluded.quest_vars, complete_count = excluded.complete_count",
            params![character_id as i64, quest_id as i64, status, quest_vars as i64, complete_count as i64],
        )?;
        Ok(())
    }

    /// Salva estado da quest usando tipos numéricos
    pub fn save_quest(
        conn: &Connection,
        character_id: u32,
        quest_id: u32,
        status: u8,
        flags: u32,
        vars: [u32; 4],
        _start_ts: u32,
    ) -> Result<()> {
        let status_str = match status {
            0 => "START",
            1 => "COMPLETE",
            _ => "REWARD",
        };
        Self::salvar_quest(conn, character_id, quest_id, status_str, vars[0], flags)
    }

    /// Retorna todas as missões ativas ou concluídas do personagem
    pub fn quests_do_personagem(conn: &Connection, character_id: u32) -> Result<Vec<QuestPersistida>> {
        let mut stmt = conn.prepare(
            "SELECT quest_id, status, quest_vars, complete_count FROM player_quests WHERE character_id = ?1",
        )?;
        let rows = stmt.query_map(params![character_id as i64], |row| {
            Ok(QuestPersistida {
                quest_id: row.get::<_, i64>(0)? as u32,
                status: row.get(1)?,
                quest_vars: row.get::<_, i64>(2)? as u32,
                complete_count: row.get::<_, i64>(3)? as u32,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    /// Salva em lote missões do jogador via transação
    pub fn salvar_quests(conn: &Connection, character_id: u32, quests: &[QuestPersistida]) -> Result<()> {
        let mut tx = conn.unchecked_transaction()?;
        for q in quests {
            tx.execute(
                "INSERT INTO player_quests (character_id, quest_id, status, quest_vars, complete_count)
                 VALUES (?1, ?2, ?3, ?4, ?5)
                 ON CONFLICT(character_id, quest_id) DO UPDATE SET
                    status = excluded.status,
                    quest_vars = excluded.quest_vars,
                    complete_count = excluded.complete_count",
                params![
                    character_id as i64,
                    q.quest_id as i64,
                    &q.status,
                    q.quest_vars as i64,
                    q.complete_count as i64,
                ],
            )?;
        }
        tx.commit()
    }

    /// Carrega missões persistidas do jogador
    pub fn carregar_quests(conn: &Connection, character_id: u32) -> Result<Vec<QuestPersistida>> {
        Self::quests_do_personagem(conn, character_id)
    }
}
