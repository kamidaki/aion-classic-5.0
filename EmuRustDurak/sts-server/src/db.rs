use rand::RngCore;
use rusqlite::{params, Connection, Result};
use std::path::Path;
use std::sync::Mutex;

pub struct Db {
    conn: Mutex<Connection>,
}

impl Db {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self {
            conn: Mutex::new(conn),
        };
        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        self.conn.lock().unwrap().execute_batch(
            "
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                issued_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            ",
        )
    }

    /// Ensure an account exists, generate a random session token, persist the
    /// (token → username) mapping, and return the token as an uppercase UUID
    /// string in the form the Aion client expects.
    pub fn issue_session(&self, username: &str) -> Result<String> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR IGNORE INTO accounts(username) VALUES (?1)",
            params![username],
        )?;
        let token = random_uuid_string();
        conn.execute(
            "INSERT INTO sessions(token, username) VALUES (?1, ?2)",
            params![token, username],
        )?;
        Ok(token)
    }
}

/// Generate a UUID-4-ish string (format `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`)
/// suitable for the static-TOKEN slot in the STS reply. We don't need RFC 4122
/// compliance — the game client only treats this as an opaque identifier.
fn random_uuid_string() -> String {
    let mut bytes = [0u8; 16];
    rand::thread_rng().fill_bytes(&mut bytes);
    format!(
        "{:02X}{:02X}{:02X}{:02X}-{:02X}{:02X}-{:02X}{:02X}-{:02X}{:02X}-{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}",
        bytes[0], bytes[1], bytes[2], bytes[3],
        bytes[4], bytes[5],
        bytes[6], bytes[7],
        bytes[8], bytes[9],
        bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15],
    )
}
