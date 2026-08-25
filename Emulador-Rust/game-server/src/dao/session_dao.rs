use rusqlite::{params, Connection, Result};

pub struct SessionDao;

impl SessionDao {
    /// Busca o nome da conta associado ao token de sessão
    pub fn lookup_session(conn: &Connection, token: &str) -> Result<Option<String>> {
        let token = token.trim_end_matches(' ').trim();

        conn.query_row(
            "SELECT COALESCE(NULLIF(account_name, ''), username) FROM sessions WHERE token = ?1 OR session_key = ?1",
            params![token],
            |row| row.get::<_, String>(0),
        )
        .map(Some)
        .or_else(|e| match e {
            rusqlite::Error::QueryReturnedNoRows => Ok(None),
            other => Err(other),
        })
    }

    /// Valida o par (account_id, session_key) e retorna o nome da conta ativa
    pub fn resolver_sessao(conn: &Connection, account_id: u32, session_key: u32) -> Result<Option<String>> {
        let agora = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0);

        // 1. Tenta na tabela sessions local
        let res: Option<String> = conn
            .query_row(
                "SELECT COALESCE(NULLIF(account_name, ''), username) FROM sessions
                 WHERE account_id = ?1 AND session_key = ?2
                   AND (expires_at = 0 OR expires_at >= ?3)
                 ORDER BY created_at DESC LIMIT 1",
                params![account_id as i64, session_key as i64, agora],
                |row| row.get::<_, String>(0),
            )
            .ok();

        if let Some(name) = res {
            return Ok(Some(name));
        }

        // 2. Tenta na tabela account_data local por account_id
        let acc_name: Option<String> = conn
            .query_row(
                "SELECT name FROM account_data WHERE id = ?1",
                params![account_id as i64],
                |row| row.get::<_, String>(0),
            )
            .ok();

        if let Some(name) = acc_name {
            return Ok(Some(name));
        }

        // 3. Tenta consultar login.db se presente no disco
        let login_paths = ["data/Banco de Dados/login.db", "../Produto Final/data/Banco de Dados/login.db"];
        for p in &login_paths {
            let path = std::path::Path::new(p);
            if path.exists() {
                if let Ok(l_conn) = Connection::open(path) {
                    if let Ok(name) = l_conn.query_row(
                        "SELECT COALESCE(NULLIF(account_name, ''), username) FROM sessions
                         WHERE account_id = ?1 AND session_key = ?2
                         ORDER BY id DESC LIMIT 1",
                        params![account_id as i64, session_key as i64],
                        |row| row.get::<_, String>(0),
                    ) {
                        return Ok(Some(name));
                    }
                    if let Ok(name) = l_conn.query_row(
                        "SELECT name FROM account_data WHERE id = ?1",
                        params![account_id as i64],
                        |row| row.get::<_, String>(0),
                    ) {
                        return Ok(Some(name));
                    }
                }
            }
        }

        Ok(None)
    }
}
