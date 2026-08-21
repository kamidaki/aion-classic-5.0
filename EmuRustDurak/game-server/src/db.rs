use rusqlite::{params, Connection, Result};
use std::path::Path;

pub struct Db {
    conn: Connection,
}

pub struct PersistedCharacter {
    pub id: u32,
    pub account_id: i64,
    pub name: String,
    pub level: u16,
    pub exp: u64,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub hp: i32,
    pub mp: u32,
}

impl Db {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            "
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL REFERENCES accounts(id),
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                exp INTEGER NOT NULL DEFAULT 0,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL,
                hp INTEGER NOT NULL DEFAULT 100,
                mp INTEGER NOT NULL DEFAULT 100,
                updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                issued_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            ",
        )
    }

    /// Look up the username associated with a session token. Returns None if
    /// the token is unknown (e.g. client connected directly without going
    /// through STS).
    pub fn lookup_session(&self, token: &str) -> Result<Option<String>> {
        self.conn
            .query_row(
                "SELECT username FROM sessions WHERE token = ?1",
                params![token],
                |row| row.get::<_, String>(0),
            )
            .map(Some)
            .or_else(|e| match e {
                rusqlite::Error::QueryReturnedNoRows => Ok(None),
                other => Err(other),
            })
    }

    /// Ensures an account exists for the given username (creates if missing),
    /// then loads the first character for that account, creating a default
    /// character with the classic hardcoded starting values if none exists.
    /// Personagem novo nasce no ponto de entrada de [`crate::game::mundo`] -- as coordenadas que
    /// vinham daqui eram da 2.5 e nao correspondem a mapa nenhum da 4.5.
    pub fn load_or_create_character(
        &self,
        username: &str,
    ) -> Result<PersistedCharacter> {
        use crate::game::mundo;

        self.conn.execute(
            "INSERT OR IGNORE INTO accounts(username) VALUES (?1)",
            params![username],
        )?;
        let account_id: i64 = self.conn.query_row(
            "SELECT id FROM accounts WHERE username = ?1",
            params![username],
            |row| row.get(0),
        )?;

        let existing: Option<PersistedCharacter> = self
            .conn
            .query_row(
                "SELECT id, account_id, name, level, exp, x, y, z, hp, mp
                 FROM characters WHERE account_id = ?1 LIMIT 1",
                params![account_id],
                |row| {
                    Ok(PersistedCharacter {
                        id: row.get::<_, i64>(0)? as u32,
                        account_id: row.get(1)?,
                        name: row.get(2)?,
                        level: row.get::<_, i64>(3)? as u16,
                        exp: row.get::<_, i64>(4)? as u64,
                        x: row.get(5)?,
                        y: row.get(6)?,
                        z: row.get(7)?,
                        hp: row.get::<_, i64>(8)? as i32,
                        mp: row.get::<_, i64>(9)? as u32,
                    })
                },
            )
            .ok();

        if let Some(c) = existing {
            return Ok(c);
        }

        self.conn.execute(
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, hp, mp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                account_id,
                "Azphelumbra",
                14_i64,
                226_334_i64,
                mundo::X,
                mundo::Y,
                mundo::Z,
                1148_i64,
                1080_i64,
            ],
        )?;
        let id = self.conn.last_insert_rowid() as u32;

        Ok(PersistedCharacter {
            id,
            account_id,
            name: "Azphelumbra".into(),
            level: 14,
            exp: 226_334,
            x: mundo::X,
            y: mundo::Y,
            z: mundo::Z,
            hp: 1148,
            mp: 1080,
        })
    }

    pub fn save_character(
        &self,
        id: u32,
        x: f32,
        y: f32,
        z: f32,
        level: u16,
        exp: u64,
        hp: i32,
        mp: u32,
    ) -> Result<()> {
        self.conn.execute(
            "UPDATE characters
             SET x=?1, y=?2, z=?3, level=?4, exp=?5, hp=?6, mp=?7,
                 updated_at=strftime('%s','now')
             WHERE id=?8",
            params![
                x,
                y,
                z,
                level as i64,
                exp as i64,
                hp as i64,
                mp as i64,
                id as i64
            ],
        )?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn in_memory() -> Db {
        let conn = Connection::open_in_memory().unwrap();
        let db = Db { conn };
        db.init_schema().unwrap();
        db
    }

    #[test]
    fn load_or_create_is_idempotent_and_persists_updates() {
        let db = in_memory();

        let a = db.load_or_create_character("alice").unwrap();
        assert_eq!(a.name, "Azphelumbra");
        assert_eq!(a.level, 14);
        assert_eq!(a.x, crate::game::mundo::X, "personagem novo nasce no ponto de entrada");

        let b = db.load_or_create_character("alice").unwrap();
        assert_eq!(a.id, b.id, "second call must return same character id");
        assert_eq!(a.account_id, b.account_id);

        db.save_character(a.id, 100.0, 200.0, 300.0, 20, 999_999, 500, 250)
            .unwrap();

        let c = db.load_or_create_character("alice").unwrap();
        assert_eq!(c.id, a.id);
        assert_eq!(c.level, 20);
        assert_eq!(c.exp, 999_999);
        assert_eq!(c.x, 100.0);
        assert_eq!(c.y, 200.0);
        assert_eq!(c.z, 300.0);
        assert_eq!(c.hp, 500);
        assert_eq!(c.mp, 250);
    }

    #[test]
    fn different_usernames_get_different_accounts_and_characters() {
        let db = in_memory();
        let a = db.load_or_create_character("alice").unwrap();
        let b = db.load_or_create_character("bob").unwrap();
        assert_ne!(a.account_id, b.account_id);
        assert_ne!(a.id, b.id);
    }
}
