use rusqlite::{params, Connection, Result};
use std::path::Path;
use std::sync::Mutex;

pub struct AuthDb {
    conn: Mutex<Connection>,
}

impl AuthDb {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self {
            conn: Mutex::new(conn),
        };
        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute_batch(
            "
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                access_level INTEGER NOT NULL DEFAULT 0,
                membership INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                issued_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
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
                aparencia BLOB,
                updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);
            ",
        )
    }

    pub fn get_or_create_account(&self, username: &str, auto_create: bool) -> Result<Option<i64>> {
        let conn = self.conn.lock().unwrap();
        let existing: Result<i64, _> = conn.query_row(
            "SELECT id FROM accounts WHERE username = ?1",
            params![username],
            |row| row.get(0),
        );

        match existing {
            Ok(id) => Ok(Some(id)),
            Err(rusqlite::Error::QueryReturnedNoRows) => {
                if auto_create {
                    conn.execute(
                        "INSERT INTO accounts(username) VALUES (?1)",
                        params![username],
                    )?;
                    let id = conn.last_insert_rowid();
                    println!("INFO: [AuthDb] Auto-created account '{username}' (id: {id})");
                    Ok(Some(id))
                } else {
                    Ok(None)
                }
            }
            Err(e) => Err(e),
        }
    }

    pub fn count_characters(&self, account_id: i64) -> u8 {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT COUNT(*) FROM characters WHERE account_id = ?1",
            params![account_id],
            |row| row.get::<_, i64>(0),
        )
        .map(|count| count.min(255) as u8)
        .unwrap_or(0)
    }

    pub fn register_session(&self, token: &str, username: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR REPLACE INTO sessions(token, username) VALUES (?1, ?2)",
            params![token, username],
        )?;
        Ok(())
    }
}
