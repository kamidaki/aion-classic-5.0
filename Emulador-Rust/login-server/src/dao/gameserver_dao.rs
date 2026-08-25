use rusqlite::{Connection, Result};

#[derive(Debug, Clone)]
pub struct GameServerRecord {
    pub id: u8,
    pub mask: String,
    pub password: String,
    pub port: u16,
}

pub struct GameServerDao;

impl GameServerDao {
    pub fn get_all(conn: &Connection) -> Result<Vec<GameServerRecord>> {
        let mut stmt = conn.prepare("SELECT id, mask, password FROM gameservers ORDER BY id")?;
        let rows = stmt.query_map([], |row| {
            Ok(GameServerRecord {
                id: row.get::<_, i64>(0)? as u8,
                mask: row.get(1)?,
                password: row.get(2)?,
                port: 7777,
            })
        })?;
        let mut servers = Vec::new();
        for r in rows {
            servers.push(r?);
        }
        Ok(servers)
    }
}
