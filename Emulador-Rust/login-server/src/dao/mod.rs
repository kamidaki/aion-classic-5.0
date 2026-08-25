//! Data Access Object (DAO) layer for Login Server.

pub mod account_dao;
pub mod gameserver_dao;
pub mod session_dao;

pub use account_dao::{Account, AccountDao, encode_password};
pub use gameserver_dao::{GameServerDao, GameServerRecord};
pub use session_dao::SessionDao;

use parking_lot::Mutex;
use rusqlite::{Connection, Result};
use std::sync::Arc;

pub struct AuthDb {
    conn: Arc<Mutex<Connection>>,
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
                 heading INTEGER NOT NULL DEFAULT 0,
                 world_id INTEGER NOT NULL DEFAULT 110070000,
                 gender INTEGER NOT NULL DEFAULT 0,
                 race INTEGER NOT NULL DEFAULT 0,
                 player_class INTEGER NOT NULL DEFAULT 0,
                 creation_date INTEGER NOT NULL DEFAULT 0,
                 deleted INTEGER NOT NULL DEFAULT 0
             );
             CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);",
        )?;

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

    pub fn authenticate_or_create_account(
        &self,
        name: &str,
        password: &str,
        auto_create: bool,
    ) -> Result<Option<Account>> {
        let conn = self.conn.lock();
        AccountDao::authenticate_or_create(&conn, name, password, auto_create)
    }

    pub fn get_or_create_account(&self, name: &str, auto_create: bool) -> Result<Option<Account>> {
        self.authenticate_or_create_account(name, "", auto_create)
    }

    pub fn get_character_count(&self, account_name: &str) -> u8 {
        let conn = self.conn.lock();
        AccountDao::get_character_count(&conn, account_name)
    }

    pub fn issue_session(&self, account_id: u32, account_name: &str, session_key: u32) -> Result<String> {
        let conn = self.conn.lock();
        SessionDao::issue_session(&conn, account_id, account_name, session_key)
    }

    pub fn register_token(&self, token: &str, account_name: &str) -> Result<()> {
        let conn = self.conn.lock();
        SessionDao::register_token(&conn, token, account_name)
    }

    pub fn get_game_servers(&self) -> Result<Vec<GameServerRecord>> {
        let conn = self.conn.lock();
        GameServerDao::get_all(&conn)
    }
}
