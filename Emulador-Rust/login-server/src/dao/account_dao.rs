use base64::Engine;
use rusqlite::{params, Connection, Result};
use sha1::{Digest, Sha1};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct Account {
    pub id: i64,
    pub name: String,
    pub access_level: i32,
    pub membership: i32,
}

pub fn encode_password(password: &str) -> String {
    let mut hasher = Sha1::new();
    hasher.update(password.as_bytes());
    base64::engine::general_purpose::STANDARD.encode(hasher.finalize())
}

pub struct AccountDao;

impl AccountDao {
    pub fn authenticate_or_create(
        conn: &Connection,
        name: &str,
        password: &str,
        auto_create: bool,
    ) -> Result<Option<Account>> {
        let trimmed_name = name.trim();
        if trimmed_name.is_empty() {
            return Ok(None);
        }

        let mut stmt = conn.prepare("SELECT id, name, password, access_level, membership FROM account_data WHERE name = ?1 COLLATE NOCASE")?;
        let mut rows = stmt.query(params![trimmed_name])?;

        if let Some(row) = rows.next()? {
            let id: i64 = row.get(0)?;
            let acc_name: String = row.get(1)?;
            let db_pass: String = row.get(2)?;
            let access_level: i32 = row.get(3)?;
            let membership: i32 = row.get(4)?;

            let pass_hash = encode_password(password);
            // Valida contra o hash SHA-1 Base64 ou contra senha legada em texto puro
            if db_pass == pass_hash || db_pass == password || db_pass.is_empty() {
                // Se a senha estava em texto puro no DB, migra para o hash SHA-1 Base64 oficial
                if db_pass == password && db_pass != pass_hash && !password.is_empty() {
                    drop(rows);
                    drop(stmt);
                    let _ = conn.execute("UPDATE account_data SET password = ?1 WHERE id = ?2", params![pass_hash, id]);
                }
                println!("INFO: [AccountDao] Conta '{}' (ID: {}) autenticada com sucesso", acc_name, id);
                Ok(Some(Account {
                    id,
                    name: acc_name,
                    access_level,
                    membership,
                }))
            } else {
                println!("WARN: [AccountDao] Senha incorreta para conta '{}'", trimmed_name);
                Ok(None)
            }
        } else if auto_create {
            drop(rows);
            drop(stmt);
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
            let pass_hash = if !password.is_empty() {
                encode_password(password)
            } else {
                encode_password(trimmed_name)
            };
            conn.execute(
                "INSERT INTO account_data (name, password, access_level, membership, created_at, updated_at)
                 VALUES (?1, ?2, 0, 0, ?3, ?3)",
                params![trimmed_name, pass_hash, now],
            )?;
            let id = conn.last_insert_rowid();

            let _ = conn.execute(
                "INSERT OR REPLACE INTO account_time (account_id, last_active) VALUES (?1, ?2)",
                params![id, now],
            );

            println!("INFO: [AccountDao] Nova conta auto-criada com sucesso: '{}' (ID: {})", trimmed_name, id);

            Ok(Some(Account {
                id,
                name: trimmed_name.to_string(),
                access_level: 0,
                membership: 0,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_character_count(conn: &Connection, account_name: &str) -> u8 {
        let mut stmt = match conn.prepare(
            "SELECT COUNT(*) FROM characters WHERE account_id = (SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE)"
        ) {
            Ok(s) => s,
            Err(_) => return 0,
        };
        let count: i64 = stmt.query_row(params![account_name], |row| row.get(0)).unwrap_or(0);
        count as u8
    }
}
