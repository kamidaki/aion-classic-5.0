use rusqlite::{params, Connection, Result};
use std::time::{SystemTime, UNIX_EPOCH};

pub struct SessionDao;

impl SessionDao {
    pub fn issue_session(conn: &Connection, account_id: u32, account_name: &str, session_key: u32) -> Result<String> {
        let token = format!("{:08x}{:08x}", rand::random::<u32>(), rand::random::<u32>());
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600; // 10 minutes

        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, username, account_id, session_key, issued_at, created_at, expires_at)
             VALUES (?1, ?2, ?2, ?3, ?4, ?5, ?5, ?6)",
            params![token, account_name, account_id as i64, session_key as i64, now, expires],
        )?;

        Ok(token)
    }

    pub fn register_token(conn: &Connection, token: &str, account_name: &str) -> Result<()> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
        let expires = now + 600;
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, account_name, username, issued_at, created_at, expires_at)
             VALUES (?1, ?2, ?2, ?3, ?3, ?4)",
            params![token, account_name, now, expires],
        )?;
        Ok(())
    }
}
