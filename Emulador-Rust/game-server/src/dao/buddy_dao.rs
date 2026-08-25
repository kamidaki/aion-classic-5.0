use rusqlite::{params, Connection, Result};

pub struct BuddyDao;

impl BuddyDao {
    pub fn adicionar_amigo(conn: &Connection, player_id: u32, buddy_id: u32) -> Result<()> {
        conn.execute(
            "INSERT OR IGNORE INTO character_buddies (player_id, buddy_id) VALUES (?1, ?2)",
            params![player_id as i64, buddy_id as i64],
        )?;
        Ok(())
    }

    pub fn remover_amigo(conn: &Connection, player_id: u32, buddy_id: u32) -> Result<bool> {
        let n = conn.execute(
            "DELETE FROM character_buddies WHERE player_id = ?1 AND buddy_id = ?2",
            params![player_id as i64, buddy_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn amigos_do_personagem(conn: &Connection, player_id: u32) -> Result<Vec<crate::message::server::BuddyEntry>> {
        let mut stmt = conn.prepare(
            "SELECT c.id, c.name, c.level, c.map_id
             FROM character_buddies b
             INNER JOIN characters c ON c.id = b.buddy_id
             WHERE b.player_id = ?1",
        )?;
        let rows = stmt.query_map(params![player_id as i64], |row| {
            Ok(crate::message::server::BuddyEntry {
                player_id: row.get::<_, i64>(0)? as u32,
                name: row.get(1)?,
                is_online: true,
                map_id: row.get::<_, i64>(3)? as u32,
                level: row.get::<_, i64>(2)? as u8,
                class_id: 1,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }
}
