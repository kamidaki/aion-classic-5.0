use rusqlite::{params, Connection, Result};

pub struct AccountData {
    pub id: i64,
    pub name: String,
    pub password: String,
    pub access_level: i32,
    pub membership: i32,
    pub created_at: i64,
    pub last_ip: String,
}

pub struct AccountDao;

impl AccountDao {
    /// Insere ou garante a existência da conta
    pub fn ensure_account(conn: &Connection, username: &str) -> Result<i64> {
        conn.execute(
            "INSERT OR IGNORE INTO account_data(name, password, access_level, membership, created_at)
             VALUES (?1, ?1, 0, 0, strftime('%s','now'))",
            params![username],
        )?;
        let account_id: i64 = conn.query_row(
            "SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )?;
        Ok(account_id)
    }

    /// Busca o ID da conta por nome de usuário (case-insensitive)
    pub fn get_account_id(conn: &Connection, username: &str) -> Result<Option<i64>> {
        use rusqlite::OptionalExtension;
        conn.query_row(
            "SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )
        .optional()
    }
}
