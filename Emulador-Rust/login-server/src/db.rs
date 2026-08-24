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
             
             -- Tabela account_data oficial da referencia Aion Classic 2.4 / 4.8
             CREATE TABLE IF NOT EXISTS account_data (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL DEFAULT '',
                 activated INTEGER NOT NULL DEFAULT 1,
                 access_level INTEGER NOT NULL DEFAULT 0,
                 membership INTEGER NOT NULL DEFAULT 0,
                 old_membership INTEGER NOT NULL DEFAULT 0,
                 last_server INTEGER NOT NULL DEFAULT -1,
                 last_ip TEXT NOT NULL DEFAULT '',
                 last_mac TEXT NOT NULL DEFAULT 'xx-xx-xx-xx-xx-xx',
                 ip_force TEXT DEFAULT NULL,
                 expire INTEGER DEFAULT NULL,
                 toll INTEGER NOT NULL DEFAULT 0,
                 email TEXT DEFAULT NULL,
                 created_at INTEGER NOT NULL DEFAULT 0,
                 updated_at INTEGER NOT NULL DEFAULT 0
             );
             
             -- Tabela account_time oficial da referencia
             CREATE TABLE IF NOT EXISTS account_time (
                 account_id INTEGER PRIMARY KEY,
                 last_active INTEGER NOT NULL DEFAULT 0,
                 expiration_time INTEGER DEFAULT NULL,
                 session_duration INTEGER DEFAULT 0,
                 accumulated_online INTEGER DEFAULT 0,
                 accumulated_rest INTEGER DEFAULT 0,
                 penalty_end INTEGER DEFAULT NULL
             );
             
             -- Tabela banned_ip oficial da referencia
             CREATE TABLE IF NOT EXISTS banned_ip (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 mask TEXT UNIQUE NOT NULL,
                 time_end INTEGER DEFAULT NULL
             );
             
             -- Tabela banned_mac oficial da referencia
             CREATE TABLE IF NOT EXISTS banned_mac (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 address TEXT UNIQUE NOT NULL,
                 details TEXT DEFAULT '',
                 time INTEGER NOT NULL DEFAULT 0
             );
             
             -- Tabela gameservers oficial da referencia
             CREATE TABLE IF NOT EXISTS gameservers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 mask TEXT NOT NULL,
                 password TEXT NOT NULL DEFAULT ''
             );
             
             -- Tabela de sessoes ativas para validacao no GameServer
             CREATE TABLE IF NOT EXISTS sessions (
                 token TEXT PRIMARY KEY,
                 username TEXT NOT NULL,
                 account_name TEXT NOT NULL,
                 account_id INTEGER NOT NULL DEFAULT 1,
                 session_key INTEGER NOT NULL DEFAULT 0,
                 issued_at INTEGER NOT NULL DEFAULT 0,
                 created_at INTEGER NOT NULL DEFAULT 0,
                 expires_at INTEGER NOT NULL DEFAULT 0
             );
             
             -- Tabela characters para contagem de chars no login
             CREATE TABLE IF NOT EXISTS characters (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 account_id INTEGER NOT NULL REFERENCES account_data(id),
                 name TEXT NOT NULL,
                 level INTEGER NOT NULL DEFAULT 1,
                 exp INTEGER NOT NULL DEFAULT 0,
                 x REAL NOT NULL DEFAULT 457.0,
                 y REAL NOT NULL DEFAULT 251.0,
                 z REAL NOT NULL DEFAULT 127.04,
                 hp INTEGER NOT NULL DEFAULT 1000,
                 mp INTEGER NOT NULL DEFAULT 1000,
                 aparencia BLOB,
                 updated_at INTEGER NOT NULL DEFAULT 0
             );
             CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);",
        )?;

        // Migracao automatica: migra dados de accounts legado para account_data e remove accounts
        let _ = conn.execute(
            "INSERT OR IGNORE INTO account_data (name, password, access_level, membership, created_at, updated_at)
             SELECT COALESCE(NULLIF(name, ''), username), password_hash, access_level, membership, created_at, updated_at FROM accounts WHERE name IS NOT NULL OR username IS NOT NULL",
            [],
        );
        let _ = conn.execute("DROP TABLE IF EXISTS accounts", []);

        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN account_name TEXT", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN username TEXT", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN session_key INTEGER NOT NULL DEFAULT 0", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN issued_at INTEGER NOT NULL DEFAULT 0", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0", []);
        let _ = conn.execute("ALTER TABLE sessions ADD COLUMN expires_at INTEGER NOT NULL DEFAULT 0", []);

        Ok(Self {
            conn: Arc::new(Mutex::new(conn)),
        })
    }

    pub fn get_or_create_account(&self, name: &str, auto_create: bool) -> Result<Option<Account>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare("SELECT id, name, access_level, membership FROM account_data WHERE name = ?1 COLLATE NOCASE")?;
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
                "INSERT INTO account_data (name, password, access_level, membership, created_at, updated_at)
                 VALUES (?1, ?1, 0, 0, ?2, ?2)",
                params![name, now],
            )?;
            let id = conn.last_insert_rowid();

            let _ = conn.execute(
                "INSERT OR REPLACE INTO account_time (account_id, last_active) VALUES (?1, ?2)",
                params![id, now],
            );

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
        let mut stmt = match conn.prepare(
            "SELECT COUNT(*) FROM characters WHERE account_id = (SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE)"
        ) {
            Ok(s) => s,
            Err(_) => return 0,
        };
        let count: i64 = stmt.query_row(params![account_name], |row| row.get(0)).unwrap_or(0);
        count as u8
    }

    pub fn issue_session(&self, account_id: u32, account_name: &str, session_key: u32) -> Result<String> {
        let token = format!("{:08x}{:08x}", rand::random::<u32>(), rand::random::<u32>());
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600; // 10 minutes

        let conn = self.conn.lock();
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, username, account_id, session_key, issued_at, created_at, expires_at)
             VALUES (?1, ?2, ?2, ?3, ?4, ?5, ?5, ?6)",
            params![token, account_name, account_id as i64, session_key as i64, now, expires],
        )?;

        Ok(token)
    }

    pub fn register_token(&self, token: &str, account_name: &str) -> Result<()> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600;
        let conn = self.conn.lock();
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, username, issued_at, created_at, expires_at)
             VALUES (?1, ?2, ?2, ?3, ?3, ?4)",
            params![token, account_name, now, expires],
        )?;
        Ok(())
    }

    pub fn get_game_servers(&self) -> Result<Vec<GameServerRecord>> {
        let conn = self.conn.lock();
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

#[derive(Debug, Clone)]
pub struct GameServerRecord {
    pub id: u8,
    pub mask: String,
    pub password: String,
    pub port: u16,
}
