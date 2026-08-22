use parking_lot::Mutex;
use rusqlite::{params, Connection, Result};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct AuthDb {
    conn: Arc<Mutex<Connection>>,
}

#[derive(Debug, Clone)]
pub struct Account {
    pub id: i64,
    pub name: String,
    pub access_level: i32,
    pub membership: i32,
}

impl AuthDb {
    pub fn open(path: &str) -> Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA busy_timeout = 5000;
             PRAGMA synchronous = NORMAL;
             
             CREATE TABLE IF NOT EXISTS accounts (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL DEFAULT '',
                 access_level INTEGER NOT NULL DEFAULT 0,
                 membership INTEGER NOT NULL DEFAULT 0,
                 created_at INTEGER NOT NULL DEFAULT 0,
                 last_ip TEXT NOT NULL DEFAULT ''
             );
             
             CREATE TABLE IF NOT EXISTS sessions (
                 token TEXT PRIMARY KEY,
                 account_name TEXT NOT NULL,
                 account_id INTEGER NOT NULL DEFAULT 1,
                 session_key INTEGER NOT NULL DEFAULT 0,
                 created_at INTEGER NOT NULL,
                 expires_at INTEGER NOT NULL
             );
             
             CREATE TABLE IF NOT EXISTS players (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 account_name TEXT NOT NULL,
                 name TEXT UNIQUE NOT NULL
             );",
        )?;

        // Ensure default developer account exists
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let _ = conn.execute(
            "INSERT OR IGNORE INTO accounts (name, password_hash, access_level, membership, created_at)
             VALUES ('teste', 'teste', 3, 2, ?1)",
            params![now],
        );

        Ok(Self {
            conn: Arc::new(Mutex::new(conn)),
        })
    }

    pub fn get_or_create_account(&self, name: &str, auto_create: bool) -> Result<Option<Account>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare("SELECT id, name, access_level, membership FROM accounts WHERE name = ?1 COLLATE NOCASE")?;
        let mut rows = stmt.query(params![name])?;

        if let Some(row) = rows.next()? {
            Ok(Some(Account {
                id: row.get(0)?,
                name: row.get(1)?,
                access_level: row.get(2)?,
                membership: row.get(3)?,
            }))
        } else if auto_create {
            drop(rows);
            drop(stmt);
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
            conn.execute(
                "INSERT INTO accounts (name, password_hash, access_level, membership, created_at) VALUES (?1, ?1, 0, 0, ?2)",
                params![name, now],
            )?;
            let id = conn.last_insert_rowid();
            Ok(Some(Account {
                id,
                name: name.to_string(),
                access_level: 0,
                membership: 0,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_character_count(&self, account_name: &str) -> u8 {
        let conn = self.conn.lock();
        let mut stmt = match conn.prepare("SELECT COUNT(*) FROM players WHERE account_name = ?1 COLLATE NOCASE") {
            Ok(s) => s,
            Err(_) => return 0,
        };
        let count: i64 = stmt.query_row(params![account_name], |row| row.get(0)).unwrap_or(0);
        count as u8
    }

    pub fn issue_session(&self, account_name: &str, session_key: u32) -> Result<String> {
        let token = format!("{:08x}{:08x}", rand::random::<u32>(), rand::random::<u32>());
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600; // 10 minutes

        let conn = self.conn.lock();
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, session_key, created_at, expires_at)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![token, account_name, session_key as i64, now, expires],
        )?;

        Ok(token)
    }

    pub fn register_token(&self, token: &str, account_name: &str) -> Result<()> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600;
        let conn = self.conn.lock();
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, created_at, expires_at)
             VALUES (?1, ?2, ?3, ?4)",
            params![token, account_name, now, expires],
        )?;
        Ok(())
    }
}
