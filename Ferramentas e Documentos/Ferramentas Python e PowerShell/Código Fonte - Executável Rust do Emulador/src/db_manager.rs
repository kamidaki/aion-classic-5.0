use mysql::prelude::*;
use mysql::{OptsBuilder, Pool, Row};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Instant;
use crate::config::DatabaseSettings;

const EMBEDDED_SQL_CS: &str = include_str!("../../../../Emulador - Produto Final/ChatServer/sql/aion_cs.sql");
const EMBEDDED_SQL_LS: &str = include_str!("../../../../Emulador - Produto Final/LoginServer/sql/aion_ls.sql");
const EMBEDDED_SQL_GS: &str = include_str!("../../../../Emulador - Produto Final/GameServer/sql/aion_gs.sql");

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DbCheckResult {
    pub id: String,
    pub server_name: String,
    pub db_name: String,
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub properties_file: String,
    pub connected: bool,
    pub db_exists: bool,
    pub tables_exist: bool,
    pub table_count: usize,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColumnInfo {
    pub cid: i64,
    pub name: String,
    pub type_name: String,
    pub notnull: bool,
    pub dflt_value: Option<String>,
    pub pk: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableSchema {
    pub db_id: String,
    pub name: String,
    pub row_count: i64,
    pub columns: Vec<ColumnInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseGroup {
    pub id: String,
    pub name: String,
    pub filename: String,
    pub size_bytes: u64,
    pub table_count: usize,
    pub total_rows: i64,
    pub tables: Vec<TableSchema>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableDataResult {
    pub db_id: String,
    pub table: String,
    pub columns: Vec<ColumnInfo>,
    pub pk_columns: Vec<String>,
    pub rows: Vec<HashMap<String, Value>>,
    pub total_rows: i64,
    pub page: usize,
    pub limit: usize,
    pub total_pages: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryResult {
    pub is_select: bool,
    pub columns: Vec<String>,
    pub rows: Vec<Vec<Value>>,
    pub affected_rows: usize,
    pub execution_time_ms: f64,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct OnlinePlayerInfo {
    pub id: i64,
    pub name: String,
    pub account_name: String,
    pub class_name: String,
    pub race: String,
    pub exp: i64,
}

fn mysql_val_to_json(val: &mysql::Value) -> Value {
    match val {
        mysql::Value::NULL => Value::Null,
        mysql::Value::Bytes(b) => {
            Value::String(String::from_utf8_lossy(b).to_string())
        }
        mysql::Value::Int(i) => serde_json::json!(i),
        mysql::Value::UInt(u) => serde_json::json!(u),
        mysql::Value::Float(f) => serde_json::json!(f),
        mysql::Value::Double(d) => serde_json::json!(d),
        mysql::Value::Date(y, m, d, h, min, s, _) => {
            Value::String(format!("{:04}-{:02}-{:02} {:02}:{:02}:{:02}", y, m, d, h, min, s))
        }
        mysql::Value::Time(is_neg, d, h, min, s, _) => {
            let sign = if *is_neg { "-" } else { "" };
            Value::String(format!("{}{:02}:{:02}:{:02}", sign, d * 24 + (*h as u32), min, s))
        }
    }
}

fn row_get_str(r: &Row, idx: usize) -> Option<String> {
    match r.as_ref(idx) {
        Some(mysql::Value::NULL) | None => None,
        Some(mysql::Value::Bytes(b)) => Some(String::from_utf8_lossy(b).to_string()),
        Some(mysql::Value::Int(i)) => Some(i.to_string()),
        Some(mysql::Value::UInt(u)) => Some(u.to_string()),
        Some(mysql::Value::Float(f)) => Some(f.to_string()),
        Some(mysql::Value::Double(d)) => Some(d.to_string()),
        Some(mysql::Value::Date(y, m, d, h, min, s, _)) => {
            Some(format!("{:04}-{:02}-{:02} {:02}:{:02}:{:02}", y, m, d, h, min, s))
        }
        Some(mysql::Value::Time(is_neg, d, h, min, s, _)) => {
            let sign = if *is_neg { "-" } else { "" };
            Some(format!("{}{:02}:{:02}:{:02}", sign, d * 24 + (*h as u32), min, s))
        }
    }
}

fn row_get_str_or_default(r: &Row, idx: usize) -> String {
    row_get_str(r, idx).unwrap_or_default()
}

fn row_get_i64(r: &Row, idx: usize) -> i64 {
    match r.as_ref(idx) {
        Some(mysql::Value::Int(i)) => *i,
        Some(mysql::Value::UInt(u)) => *u as i64,
        Some(mysql::Value::Bytes(b)) => {
            String::from_utf8_lossy(b).trim().parse::<i64>().unwrap_or(0)
        }
        _ => 0,
    }
}

#[derive(Clone)]
pub struct DbManager {
    pool: Arc<RwLock<Option<Arc<Pool>>>>,
    pub db_name: String,
    pub host: String,
    pub port: u16,
    pub user: String,
    pub pass: String,
    pub properties_file: String,
}

impl DbManager {
    pub fn new(cfg_db: &DatabaseSettings) -> Self {
        let (host, port, user, pass, db_name, prop_file) = Self::resolve_db_credentials(cfg_db);
        let pool = DbManager::try_create_pool(&host, port, &user, &pass, &db_name);
        Self {
            pool: Arc::new(RwLock::new(pool)),
            db_name,
            host,
            port,
            user,
            pass,
            properties_file: prop_file,
        }
    }

    /// Like `new`, but uses `cfg_db.properties_file` as a prioritized candidate if set.
    pub fn new_with_properties_hint(cfg_db: &DatabaseSettings) -> Self {
        if !cfg_db.properties_file.is_empty() {
            let mut candidates = Vec::new();
            if let Ok(exe_path) = std::env::current_exe() {
                if let Some(exe_dir) = exe_path.parent() {
                    candidates.push(exe_dir.join(&cfg_db.properties_file));
                }
            }
            candidates.push(PathBuf::from(&cfg_db.properties_file));

            for p in &candidates {
                if let Ok(content) = std::fs::read_to_string(p) {
                    let (host, port, user, pass, db_name) = DbManager::parse_db_properties(&content, cfg_db);
                    let pool = DbManager::try_create_pool(&host, port, &user, &pass, &db_name);
                    return Self {
                        pool: Arc::new(RwLock::new(pool)),
                        db_name,
                        host,
                        port,
                        user,
                        pass,
                        properties_file: p.to_string_lossy().to_string(),
                    };
                }
            }
        }
        DbManager::new(cfg_db)
    }

    pub fn get_pool(&self) -> Option<Arc<Pool>> {
        self.pool.read().clone()
    }

    /// Parse database.properties file content and return (host, port, user, pass, db_name)
    fn parse_db_properties(content: &str, cfg_db: &DatabaseSettings) -> (String, u16, String, String, String) {
        let mut url = String::new();
        let mut user = String::new();
        let mut pass = String::new();

        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with('#') || !trimmed.contains('=') {
                continue;
            }
            let parts: Vec<&str> = trimmed.splitn(2, '=').collect();
            let k = parts[0].trim();
            let v = parts[1].trim();

            if k == "database.url" {
                url = v.to_string();
            } else if k == "database.user" {
                user = v.to_string();
            } else if k == "database.password" {
                pass = v.to_string();
            }
        }

        if !url.is_empty() {
            let mut host = "127.0.0.1".to_string();
            let mut port = 3306u16;
            let mut db = cfg_db.database.clone();

            if let Some(after_scheme) = url.strip_prefix("jdbc:mysql://") {
                let host_and_rest = after_scheme.split('?').next().unwrap_or(after_scheme);
                if let Some((hp, db_part)) = host_and_rest.split_once('/') {
                    db = db_part.to_string();
                    if let Some((h, p)) = hp.split_once(':') {
                        host = h.to_string();
                        if let Ok(parsed_p) = p.parse::<u16>() {
                            port = parsed_p;
                        }
                    } else {
                        host = hp.to_string();
                    }
                }
            }

            return (host, port, user, pass, db);
        }

        (cfg_db.host.clone(), cfg_db.port, cfg_db.user.clone(), cfg_db.password.clone(), cfg_db.database.clone())
    }

    /// Create a MySQL pool and test the connection
    fn try_create_pool(host: &str, port: u16, user: &str, pass: &str, db_name: &str) -> Option<Arc<Pool>> {
        if host.is_empty() || user.is_empty() {
            return None;
        }
        let opts = OptsBuilder::new()
            .ip_or_hostname(Some(host))
            .tcp_port(port)
            .user(Some(user))
            .pass(Some(pass))
            .db_name(Some(db_name))
            .prefer_socket(false);
        match Pool::new(opts) {
            Ok(p) => match p.get_conn() {
                Ok(_) => {
                    eprintln!("[DbManager] Conectado com sucesso: {}:{}/{}", host, port, db_name);
                    Some(Arc::new(p))
                }
                Err(e) => {
                    eprintln!("[DbManager] Erro autenticação {}:{}/{}: {}", host, port, db_name, e);
                    None
                }
            },
            Err(e) => {
                eprintln!("[DbManager] Erro pool {}:{}/{}: {}", host, port, db_name, e);
                None
            }
        }
    }

    fn resolve_db_credentials(cfg_db: &DatabaseSettings) -> (String, u16, String, String, String, String) {
        if !cfg_db.auto_read_properties && !cfg_db.host.is_empty() && !cfg_db.user.is_empty() {
            return (
                cfg_db.host.clone(),
                cfg_db.port,
                cfg_db.user.clone(),
                cfg_db.password.clone(),
                cfg_db.database.clone(),
                cfg_db.properties_file.clone(),
            );
        }

        let mut candidates = Vec::new();
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                if !cfg_db.properties_file.is_empty() {
                    candidates.push(exe_dir.join(&cfg_db.properties_file));
                }
                candidates.push(exe_dir.join("GameServer/config/network/database.properties"));
                candidates.push(exe_dir.join("LoginServer/config/network/database.properties"));
                candidates.push(exe_dir.join("ChatServer/config/network/database.properties"));
                candidates.push(exe_dir.join("../Emulador - Produto Final/GameServer/config/network/database.properties"));
            }
        }
        if !cfg_db.properties_file.is_empty() {
            candidates.push(PathBuf::from(&cfg_db.properties_file));
        }
        candidates.push(PathBuf::from("GameServer/config/network/database.properties"));
        candidates.push(PathBuf::from("LoginServer/config/network/database.properties"));
        candidates.push(PathBuf::from("ChatServer/config/network/database.properties"));
        candidates.push(PathBuf::from("Emulador - Produto Final/GameServer/config/network/database.properties"));

        for p in &candidates {
            if let Ok(content) = fs::read_to_string(p) {
                let (host, port, user, pass, db) = Self::parse_db_properties(&content, cfg_db);
                if !host.is_empty() {
                    return (host, port, user, pass, db, p.to_string_lossy().to_string());
                }
            }
        }

        (
            cfg_db.host.clone(),
            cfg_db.port,
            cfg_db.user.clone(),
            cfg_db.password.clone(),
            cfg_db.database.clone(),
            cfg_db.properties_file.clone(),
        )
    }

    /// Check if connection to MySQL works, if database exists, and count of tables
    pub fn check_status(&self, id: &str, server_name: &str) -> DbCheckResult {
        let mut res = DbCheckResult {
            id: id.to_string(),
            server_name: server_name.to_string(),
            db_name: self.db_name.clone(),
            host: self.host.clone(),
            port: self.port,
            user: self.user.clone(),
            password: self.pass.clone(),
            properties_file: self.properties_file.clone(),
            connected: false,
            db_exists: false,
            tables_exist: false,
            table_count: 0,
            error: None,
        };

        if self.host.is_empty() || self.user.is_empty() {
            res.error = Some("Host ou usuário não configurados no arquivo de propriedades.".to_string());
            return res;
        }

        // Test connecting to MySQL server directly without specifying a database
        let base_opts = OptsBuilder::new()
            .ip_or_hostname(Some(&self.host))
            .tcp_port(self.port)
            .user(Some(&self.user))
            .pass(Some(&self.pass))
            .prefer_socket(false);

        let base_pool = match Pool::new(base_opts) {
            Ok(p) => p,
            Err(e) => {
                res.error = Some(format!("{}", e));
                return res;
            }
        };

        let mut conn = match base_pool.get_conn() {
            Ok(c) => c,
            Err(e) => {
                res.error = Some(format!("{}", e));
                return res;
            }
        };

        res.connected = true;

        // Check if database exists
        let check_db_sql = format!(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{}'",
            self.db_name
        );
        match conn.query_first::<String, _>(&check_db_sql) {
            Ok(Some(_)) => {
                res.db_exists = true;
            }
            Ok(None) => {
                res.db_exists = false;
                return res;
            }
            Err(e) => {
                res.error = Some(format!("Erro ao checar database: {}", e));
                return res;
            }
        }

        // Count tables
        let count_tables_sql = format!(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{}'",
            self.db_name
        );
        match conn.query_first::<i64, _>(&count_tables_sql) {
            Ok(Some(count)) => {
                let cnt = count.max(0) as usize;
                res.table_count = cnt;
                res.tables_exist = cnt > 0;
            }
            Ok(None) => {
                res.table_count = 0;
                res.tables_exist = false;
            }
            Err(e) => {
                res.error = Some(format!("Erro ao contar tabelas: {}", e));
            }
        }

        res
    }

    /// Automatically create database and tables from SQL template
    pub fn create_database_and_tables(&self, id: &str) -> Result<usize, String> {
        if self.host.is_empty() || self.user.is_empty() {
            return Err("Host ou usuário não configurados no arquivo de propriedades.".to_string());
        }

        let base_opts = OptsBuilder::new()
            .ip_or_hostname(Some(&self.host))
            .tcp_port(self.port)
            .user(Some(&self.user))
            .pass(Some(&self.pass))
            .prefer_socket(false);

        let base_pool = Pool::new(base_opts).map_err(|e| format!("Erro ao conectar no MySQL: {}", e))?;
        let mut conn = base_pool.get_conn().map_err(|e| format!("Erro ao obter conexão MySQL: {}", e))?;

        let create_db_sql = format!(
            "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            self.db_name
        );
        conn.query_drop(&create_db_sql).map_err(|e| format!("Erro ao criar database '{}': {}", self.db_name, e))?;

        // Connect directly to the new database
        let db_opts = OptsBuilder::new()
            .ip_or_hostname(Some(&self.host))
            .tcp_port(self.port)
            .user(Some(&self.user))
            .pass(Some(&self.pass))
            .db_name(Some(&self.db_name))
            .prefer_socket(false);

        let db_pool = Pool::new(db_opts).map_err(|e| format!("Erro ao conectar ao novo banco '{}': {}", self.db_name, e))?;
        let mut db_conn = db_pool.get_conn().map_err(|e| format!("Erro de sessão no novo banco '{}': {}", self.db_name, e))?;

        let sql_content = Self::load_sql_content(id)?;
        let statements = Self::split_sql_statements(&sql_content);
        let mut created_count = 0;

        for stmt in statements {
            let s = stmt.trim();
            if s.is_empty() {
                continue;
            }
            if let Err(e) = db_conn.query_drop(s) {
                eprintln!("[DbManager] Aviso ao executar SQL na criação ({}): {}", self.db_name, e);
            } else if s.to_uppercase().starts_with("CREATE TABLE") {
                created_count += 1;
            }
        }

        *self.pool.write() = Some(Arc::new(db_pool));
        eprintln!("[DbManager] Banco '{}' criado com sucesso! Tabelas criadas: {}", self.db_name, created_count);

        Ok(created_count)
    }

    fn load_sql_content(id: &str) -> Result<String, String> {
        let (file_name, srv_folder, embedded) = match id {
            "cs" | "chat" => ("aion_cs.sql", "ChatServer", EMBEDDED_SQL_CS),
            "ls" | "login" => ("aion_ls.sql", "LoginServer", EMBEDDED_SQL_LS),
            _ => ("aion_gs.sql", "GameServer", EMBEDDED_SQL_GS),
        };

        let mut candidates = Vec::new();
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                candidates.push(exe_dir.join(srv_folder).join("sql").join(file_name));
                candidates.push(exe_dir.join("sql").join(file_name));
            }
        }
        candidates.push(PathBuf::from(srv_folder).join("sql").join(file_name));
        candidates.push(PathBuf::from("sql").join(file_name));
        candidates.push(PathBuf::from(format!("{}/sql/{}", srv_folder.to_lowercase(), file_name)));

        for p in &candidates {
            if let Ok(content) = fs::read_to_string(p) {
                if !content.trim().is_empty() {
                    return Ok(content);
                }
            }
        }

        Ok(embedded.to_string())
    }

    fn split_sql_statements(sql: &str) -> Vec<String> {
        let mut stmts = Vec::new();
        let mut cur = String::new();
        let mut in_single_quote = false;
        let mut in_double_quote = false;
        let mut in_backtick = false;
        let mut in_line_comment = false;
        let mut in_block_comment = false;
        let chars: Vec<char> = sql.chars().collect();
        let len = chars.len();
        let mut i = 0;

        while i < len {
            let c = chars[i];
            let next_c = if i + 1 < len { Some(chars[i + 1]) } else { None };

            if in_line_comment {
                if c == '\n' {
                    in_line_comment = false;
                }
                i += 1;
                continue;
            }

            if in_block_comment {
                if c == '*' && next_c == Some('/') {
                    in_block_comment = false;
                    i += 2;
                    continue;
                }
                i += 1;
                continue;
            }

            if in_single_quote {
                cur.push(c);
                if c == '\\' && i + 1 < len {
                    i += 1;
                    cur.push(chars[i]);
                } else if c == '\'' {
                    in_single_quote = false;
                }
                i += 1;
                continue;
            }

            if in_double_quote {
                cur.push(c);
                if c == '\\' && i + 1 < len {
                    i += 1;
                    cur.push(chars[i]);
                } else if c == '"' {
                    in_double_quote = false;
                }
                i += 1;
                continue;
            }

            if in_backtick {
                cur.push(c);
                if c == '`' {
                    in_backtick = false;
                }
                i += 1;
                continue;
            }

            if c == '-' && next_c == Some('-') {
                in_line_comment = true;
                i += 2;
                continue;
            }
            if c == '/' && next_c == Some('*') {
                in_block_comment = true;
                i += 2;
                continue;
            }
            if c == '#' {
                in_line_comment = true;
                i += 1;
                continue;
            }

            if c == '\'' {
                in_single_quote = true;
                cur.push(c);
                i += 1;
                continue;
            }
            if c == '"' {
                in_double_quote = true;
                cur.push(c);
                i += 1;
                continue;
            }
            if c == '`' {
                in_backtick = true;
                cur.push(c);
                i += 1;
                continue;
            }

            if c == ';' {
                let trimmed = cur.trim();
                if !trimmed.is_empty() {
                    stmts.push(trimmed.to_string());
                }
                cur.clear();
                i += 1;
                continue;
            }

            cur.push(c);
            i += 1;
        }

        let trimmed = cur.trim();
        if !trimmed.is_empty() {
            stmts.push(trimmed.to_string());
        }

        stmts
    }

    pub fn get_summary(&self) -> (bool, usize, i64) {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return (false, 0, 0),
        };

        let mut conn = match pool.get_conn() {
            Ok(c) => c,
            Err(_) => return (false, 0, 0),
        };

        let tables: Vec<String> = conn.query("SHOW TABLES").unwrap_or_default();
        let total_tables = tables.len();
        if total_tables == 0 {
            return (true, 0, 0);
        }

        // Fast exact aggregation across all tables (16ms)
        let union_inner = tables
            .iter()
            .map(|t| format!("SELECT COUNT(*) AS cnt FROM `{}`", t))
            .collect::<Vec<_>>()
            .join(" UNION ALL ");
        let query = format!("SELECT COALESCE(SUM(cnt), 0) FROM ({}) sub", union_inner);

        let count_row: Option<Row> = conn.query_first(&query).unwrap_or(None);
        let total_rows = count_row.map(|r| row_get_i64(&r, 0)).unwrap_or(0);

        (true, total_tables, total_rows)
    }

    pub fn get_all_databases_schema(&self) -> Result<Vec<DatabaseGroup>, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err(format!("Conexão MySQL ({}:{}) não configurada ou inativa.", self.host, self.port)),
        };

        let mut conn = pool.get_conn().map_err(|e| format!("Erro MySQL ao conectar: {}", e))?;

        // 1. Fetch all tables from SHOW TABLES
        let tables: Vec<String> = conn.query("SHOW TABLES").unwrap_or_default();

        // 2. Fetch all exact counts for each table via ONE single UNION ALL query (100ms)
        let mut table_counts: HashMap<String, i64> = HashMap::new();
        if !tables.is_empty() {
            let union_sql = tables
                .iter()
                .map(|t| format!("SELECT '{}' AS tbl, COUNT(*) AS cnt FROM `{}`", t, t))
                .collect::<Vec<_>>()
                .join(" UNION ALL ");

            if let Ok(c_rows) = conn.query::<Row, _>(&union_sql) {
                for cr in c_rows {
                    let tbl = row_get_str_or_default(&cr, 0);
                    let cnt = row_get_i64(&cr, 1);
                    table_counts.insert(tbl, cnt);
                }
            }
        }

        // 3. Fetch all columns for all tables in ONE query from information_schema
        let cols_query = format!(
            "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{}' ORDER BY TABLE_NAME, ORDINAL_POSITION",
            self.db_name
        );
        let col_rows: Vec<Row> = conn.query(&cols_query).unwrap_or_default();

        let mut cols_by_table: HashMap<String, Vec<ColumnInfo>> = HashMap::new();
        for r in col_rows {
            let tbl_name = row_get_str_or_default(&r, 0);
            let col_name = row_get_str_or_default(&r, 1);
            let type_name = row_get_str_or_default(&r, 2);
            let null_str = row_get_str_or_default(&r, 3);
            let key_str = row_get_str_or_default(&r, 4);
            let dflt_val = row_get_str(&r, 5);

            let list = cols_by_table.entry(tbl_name).or_insert_with(Vec::new);
            let cid = list.len() as i64;
            list.push(ColumnInfo {
                cid,
                name: col_name,
                type_name,
                notnull: null_str.to_uppercase() == "NO",
                dflt_value: dflt_val,
                pk: key_str.to_uppercase().contains("PRI"),
            });
        }

        let mut table_schemas = Vec::new();
        let mut total_rows = 0i64;

        for tbl_name in tables {
            let row_count = table_counts.get(&tbl_name).copied().unwrap_or(0);
            total_rows += row_count;

            let columns = cols_by_table.remove(&tbl_name).unwrap_or_default();

            table_schemas.push(TableSchema {
                db_id: self.db_name.clone(),
                name: tbl_name,
                row_count,
                columns,
            });
        }

        Ok(vec![DatabaseGroup {
            id: self.db_name.clone(),
            name: format!("MySQL: {}@{}:{}", self.user, self.host, self.port),
            filename: self.db_name.clone(),
            size_bytes: 0,
            table_count: table_schemas.len(),
            total_rows,
            tables: table_schemas,
        }])
    }

    pub fn get_table_data(
        &self,
        _db_id: Option<&str>,
        table: &str,
        page: usize,
        limit: usize,
        _search: Option<&str>,
        _sort_col: Option<&str>,
        _sort_order: Option<&str>,
    ) -> Result<TableDataResult, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| format!("Erro de conexão: {}", e))?;

        let cols_query = format!("SHOW COLUMNS FROM `{}`", table);
        let cols_rows: Vec<Row> = conn.query(&cols_query).map_err(|e| e.to_string())?;

        let mut columns = Vec::new();
        let mut pk_columns = Vec::new();

        for (idx, r) in cols_rows.iter().enumerate() {
            let col_name = row_get_str_or_default(r, 0);
            let type_name = row_get_str_or_default(r, 1);
            let null_str = row_get_str_or_default(r, 2);
            let key_str = row_get_str_or_default(r, 3);
            let dflt_val = row_get_str(r, 4);
            let is_pk = key_str.to_uppercase().contains("PRI");

            if is_pk {
                pk_columns.push(col_name.clone());
            }

            columns.push(ColumnInfo {
                cid: idx as i64,
                name: col_name,
                type_name,
                notnull: null_str.to_uppercase() == "NO",
                dflt_value: dflt_val,
                pk: is_pk,
            });
        }

        let count_query = format!("SELECT COUNT(*) FROM `{}`", table);
        let count_row: Option<Row> = conn.query_first(&count_query).unwrap_or(None);
        let total_rows = count_row.map(|r| row_get_i64(&r, 0)).unwrap_or(0);

        let offset = page.saturating_sub(1) * limit;
        let data_query = format!("SELECT * FROM `{}` LIMIT {}, {}", table, offset, limit);
        let rows_data: Vec<Row> = conn.query(&data_query).map_err(|e| e.to_string())?;

        let mut rows = Vec::new();
        for r in rows_data {
            let mut row_map = HashMap::new();
            for (idx, col) in columns.iter().enumerate() {
                let json_val = if let Some(val) = r.as_ref(idx) {
                    mysql_val_to_json(val)
                } else {
                    Value::Null
                };
                row_map.insert(col.name.clone(), json_val);
            }
            rows.push(row_map);
        }

        let total_pages = if total_rows == 0 {
            1
        } else {
            ((total_rows as usize) + limit - 1) / limit
        };

        Ok(TableDataResult {
            db_id: self.db_name.clone(),
            table: table.to_string(),
            columns,
            pk_columns,
            rows,
            total_rows,
            page,
            limit,
            total_pages,
        })
    }

    pub fn insert_row(
        &self,
        _db_id: Option<&str>,
        table: &str,
        data: &HashMap<String, Value>,
    ) -> Result<u64, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;

        let keys: Vec<&String> = data.keys().collect();
        let cols = keys.iter().map(|k| format!("`{}`", k)).collect::<Vec<_>>().join(", ");
        let vals = keys.iter().map(|k| {
            match data.get(*k) {
                Some(Value::String(s)) => format!("'{}'", s.replace('\'', "''")),
                Some(Value::Number(n)) => n.to_string(),
                Some(Value::Bool(b)) => if *b { "1".to_string() } else { "0".to_string() },
                _ => "NULL".to_string(),
            }
        }).collect::<Vec<_>>().join(", ");

        let sql = format!("INSERT INTO `{}` ({}) VALUES ({})", table, cols, vals);
        conn.query_drop(&sql).map_err(|e| e.to_string())?;
        Ok(conn.last_insert_id())
    }

    pub fn update_row(
        &self,
        _db_id: Option<&str>,
        table: &str,
        pk: &HashMap<String, Value>,
        updates: &HashMap<String, Value>,
    ) -> Result<usize, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;

        let sets = updates.iter().map(|(k, v)| {
            let val = match v {
                Value::String(s) => format!("'{}'", s.replace('\'', "''")),
                Value::Number(n) => n.to_string(),
                Value::Bool(b) => if *b { "1".to_string() } else { "0".to_string() },
                _ => "NULL".to_string(),
            };
            format!("`{}` = {}", k, val)
        }).collect::<Vec<_>>().join(", ");

        let wheres = pk.iter().map(|(k, v)| {
            let val = match v {
                Value::String(s) => format!("'{}'", s.replace('\'', "''")),
                Value::Number(n) => n.to_string(),
                _ => "NULL".to_string(),
            };
            format!("`{}` = {}", k, val)
        }).collect::<Vec<_>>().join(" AND ");

        let sql = format!("UPDATE `{}` SET {} WHERE {}", table, sets, wheres);
        conn.query_drop(&sql).map_err(|e| e.to_string())?;
        Ok(conn.affected_rows() as usize)
    }

    pub fn delete_row(
        &self,
        _db_id: Option<&str>,
        table: &str,
        pk: &HashMap<String, Value>,
    ) -> Result<usize, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;

        let wheres = pk.iter().map(|(k, v)| {
            let val = match v {
                Value::String(s) => format!("'{}'", s.replace('\'', "''")),
                Value::Number(n) => n.to_string(),
                _ => "NULL".to_string(),
            };
            format!("`{}` = {}", k, val)
        }).collect::<Vec<_>>().join(" AND ");

        let sql = format!("DELETE FROM `{}` WHERE {}", table, wheres);
        conn.query_drop(&sql).map_err(|e| e.to_string())?;
        Ok(conn.affected_rows() as usize)
    }

    pub fn truncate_table(&self, _db_id: Option<&str>, table: &str) -> Result<(), String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;
        let _ = conn.query_drop("SET FOREIGN_KEY_CHECKS = 0");
        if let Err(_) = conn.query_drop(format!("DELETE FROM `{}`", table)) {
            let _ = conn.query_drop(format!("TRUNCATE TABLE `{}`", table));
        }
        let _ = conn.query_drop("SET FOREIGN_KEY_CHECKS = 1");
        Ok(())
    }

    pub fn clean_all_tables(&self) -> Result<Vec<String>, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;
        let tables: Vec<String> = conn.query("SHOW TABLES").map_err(|e| e.to_string())?;
        if tables.is_empty() {
            return Ok(Vec::new());
        }

        // Fast scan to find tables that actually have rows > 0
        let union_sql = tables
            .iter()
            .map(|t| format!("SELECT '{}' AS tbl, COUNT(*) AS cnt FROM `{}`", t, t))
            .collect::<Vec<_>>()
            .join(" UNION ALL ");

        let counts: Vec<Row> = conn.query(&union_sql).unwrap_or_default();
        let tables_to_clean: Vec<String> = counts
            .iter()
            .filter_map(|r| {
                let name = row_get_str_or_default(r, 0);
                let cnt = row_get_i64(r, 1);
                if cnt > 0 { Some(name) } else { None }
            })
            .collect();

        let _ = conn.query_drop("SET FOREIGN_KEY_CHECKS = 0");
        for t in &tables_to_clean {
            if let Err(_) = conn.query_drop(format!("DELETE FROM `{}`", t)) {
                let _ = conn.query_drop(format!("TRUNCATE TABLE `{}`", t));
            }
        }
        let _ = conn.query_drop("SET FOREIGN_KEY_CHECKS = 1");

        Ok(tables)
    }

    pub fn execute_query(&self, _db_id: Option<&str>, sql: &str) -> Result<QueryResult, String> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| format!("Erro de conexão: {}", e))?;
        let start = Instant::now();
        let trimmed = sql.trim();
        let is_select = trimmed.to_uppercase().starts_with("SELECT")
            || trimmed.to_uppercase().starts_with("SHOW")
            || trimmed.to_uppercase().starts_with("DESCRIBE");

        if is_select {
            let rows: Vec<Row> = conn.query(trimmed).map_err(|e| e.to_string())?;
            let duration = start.elapsed().as_secs_f64() * 1000.0;

            let mut columns = Vec::new();
            let mut result_rows = Vec::new();

            if let Some(first) = rows.first() {
                for col in first.columns_ref() {
                    columns.push(col.name_str().to_string());
                }
            }

            for r in rows {
                let mut row_vals = Vec::new();
                for idx in 0..columns.len() {
                    let json_val = if let Some(val) = r.as_ref(idx) {
                        mysql_val_to_json(val)
                    } else {
                        Value::Null
                    };
                    row_vals.push(json_val);
                }
                result_rows.push(row_vals);
            }

            Ok(QueryResult {
                is_select: true,
                columns,
                rows: result_rows,
                affected_rows: 0,
                execution_time_ms: duration,
                error: None,
            })
        } else {
            conn.query_drop(trimmed).map_err(|e| e.to_string())?;
            let duration = start.elapsed().as_secs_f64() * 1000.0;
            let affected = conn.affected_rows() as usize;

            Ok(QueryResult {
                is_select: false,
                columns: Vec::new(),
                rows: Vec::new(),
                affected_rows: affected,
                execution_time_ms: duration,
                error: None,
            })
        }
    }

    pub fn get_online_players(&self) -> Vec<OnlinePlayerInfo> {
        let pool = match self.get_pool() {
            Some(p) => p,
            None => return Vec::new(),
        };

        let mut conn = match pool.get_conn() {
            Ok(c) => c,
            Err(_) => return Vec::new(),
        };

        let query = "SELECT id, name, account_name, player_class, race, exp FROM players WHERE online = 1 ORDER BY last_online DESC LIMIT 100";
        let rows: Vec<Row> = conn.query(query).unwrap_or_default();

        let mut list = Vec::new();
        for r in rows {
            list.push(OnlinePlayerInfo {
                id: row_get_i64(&r, 0),
                name: row_get_str_or_default(&r, 1),
                account_name: row_get_str_or_default(&r, 2),
                class_name: row_get_str_or_default(&r, 3),
                race: row_get_str_or_default(&r, 4),
                exp: row_get_i64(&r, 5),
            });
        }
        list
    }
}

// ---------------------------------------------------------------------------
// DbManagerMulti — Manages GS, LS and CS databases simultaneously
// ---------------------------------------------------------------------------

/// Summary for a single named database connection (used in dashboard cards)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseSummary {
    pub id: String,
    pub label: String,
    pub color: String,
    pub is_connected: bool,
    pub engine: String,
    pub host: String,
    pub port: u16,
    pub db_name: String,
    pub user: String,
    pub total_tables: usize,
    pub total_rows: i64,
}

/// Holds 3 independent DbManager instances (gs, ls, cs)
#[derive(Clone)]
pub struct DbManagerMulti {
    pub gs: DbManager,
    pub ls: DbManager,
    pub cs: DbManager,
}

impl DbManagerMulti {
    pub fn new(databases: &std::collections::HashMap<String, DatabaseSettings>) -> Self {
        let default_db = DatabaseSettings::default();
        let gs_cfg = databases.get("gs").unwrap_or(&default_db);
        let ls_cfg = databases.get("ls").unwrap_or(&default_db);
        let cs_cfg = databases.get("cs").unwrap_or(&default_db);

        // For each named DB, if it has an explicit properties_file, override the path in resolve
        DbManagerMulti {
            gs: DbManager::new_with_properties_hint(gs_cfg),
            ls: DbManager::new_with_properties_hint(ls_cfg),
            cs: DbManager::new_with_properties_hint(cs_cfg),
        }
    }

    /// Returns summaries for all 3 databases (for dashboard cards)
    pub fn get_all_summaries(&self) -> Vec<DatabaseSummary> {
        vec![
            self.make_summary("gs", &self.gs, "Game Server (GS)", "#32CD32"),
            self.make_summary("ls", &self.ls, "Login Server (LS)", "#FFD700"),
            self.make_summary("cs", &self.cs, "Chat Server (CS)", "#00CED1"),
        ]
    }

    fn make_summary(&self, id: &str, mgr: &DbManager, label: &str, color: &str) -> DatabaseSummary {
        let (connected, tables, rows) = mgr.get_summary();
        DatabaseSummary {
            id: id.to_string(),
            label: label.to_string(),
            color: color.to_string(),
            is_connected: connected,
            engine: "MySQL".to_string(),
            host: mgr.host.clone(),
            port: mgr.port,
            db_name: mgr.db_name.clone(),
            user: mgr.user.clone(),
            total_tables: tables,
            total_rows: rows,
        }
    }

    /// Resolves which DbManager instance to target based on db_id
    pub fn resolve_mgr(&self, db_id: Option<&str>) -> &DbManager {
        match db_id {
            Some(id) if id == "ls" || id == "login" || id.contains("ls") || id.contains("login") => &self.ls,
            Some(id) if id == "cs" || id == "chat" || id.contains("cs") || id.contains("chat") => &self.cs,
            _ => &self.gs,
        }
    }

    /// Returns combined schema for all 3 databases with clear tags
    pub fn get_all_databases_schema(&self) -> Result<Vec<DatabaseGroup>, String> {
        let mut all = Vec::new();
        match self.gs.get_all_databases_schema() {
            Ok(mut dbs) => {
                for d in &mut dbs {
                    d.id = "gs".to_string();
                    d.name = format!("GameServer ({})", self.gs.db_name);
                    d.filename = self.gs.db_name.clone();
                    for t in &mut d.tables {
                        t.db_id = "gs".to_string();
                    }
                }
                all.append(&mut dbs);
            }
            Err(e) => eprintln!("[DbManagerMulti] Erro esquema GS: {}", e),
        }
        match self.ls.get_all_databases_schema() {
            Ok(mut dbs) => {
                for d in &mut dbs {
                    d.id = "ls".to_string();
                    d.name = format!("LoginServer ({})", self.ls.db_name);
                    d.filename = self.ls.db_name.clone();
                    for t in &mut d.tables {
                        t.db_id = "ls".to_string();
                    }
                }
                all.append(&mut dbs);
            }
            Err(e) => eprintln!("[DbManagerMulti] Erro esquema LS: {}", e),
        }
        match self.cs.get_all_databases_schema() {
            Ok(mut dbs) => {
                for d in &mut dbs {
                    d.id = "cs".to_string();
                    d.name = format!("ChatServer ({})", self.cs.db_name);
                    d.filename = self.cs.db_name.clone();
                    for t in &mut d.tables {
                        t.db_id = "cs".to_string();
                    }
                }
                all.append(&mut dbs);
            }
            Err(e) => eprintln!("[DbManagerMulti] Erro esquema CS: {}", e),
        }
        Ok(all)
    }

    /// Route table operations to the correct database based on db_id
    pub fn get_table_data(&self, db_id: Option<&str>, table: &str, page: usize, limit: usize, search: Option<&str>, sort_col: Option<&str>, sort_order: Option<&str>) -> Result<TableDataResult, String> {
        self.resolve_mgr(db_id).get_table_data(db_id, table, page, limit, search, sort_col, sort_order)
    }

    pub fn insert_row(&self, db_id: Option<&str>, table: &str, data: &std::collections::HashMap<String, Value>) -> Result<u64, String> {
        self.resolve_mgr(db_id).insert_row(db_id, table, data)
    }

    pub fn update_row(&self, db_id: Option<&str>, table: &str, pk: &std::collections::HashMap<String, Value>, updates: &std::collections::HashMap<String, Value>) -> Result<usize, String> {
        self.resolve_mgr(db_id).update_row(db_id, table, pk, updates)
    }

    pub fn delete_row(&self, db_id: Option<&str>, table: &str, pk: &std::collections::HashMap<String, Value>) -> Result<usize, String> {
        self.resolve_mgr(db_id).delete_row(db_id, table, pk)
    }

    pub fn truncate_table(&self, db_id: Option<&str>, table: &str) -> Result<(), String> {
        self.resolve_mgr(db_id).truncate_table(db_id, table)
    }

    pub fn execute_query(&self, db_id: Option<&str>, sql: &str) -> Result<QueryResult, String> {
        self.resolve_mgr(db_id).execute_query(db_id, sql)
    }

    pub fn clean_all_tables(&self, db_id: Option<&str>) -> Result<Vec<String>, String> {
        self.resolve_mgr(db_id).clean_all_tables()
    }

    pub fn get_online_players(&self) -> Vec<OnlinePlayerInfo> {
        self.gs.get_online_players()
    }

    pub fn check_database(&self, db_id: &str) -> DbCheckResult {
        match db_id {
            "cs" | "chat" => self.cs.check_status("cs", "Chat Server"),
            "ls" | "login" => self.ls.check_status("ls", "Login Server"),
            _ => self.gs.check_status("gs", "Game Server"),
        }
    }

    pub fn check_all_databases(&self) -> Vec<DbCheckResult> {
        vec![
            self.cs.check_status("cs", "Chat Server"),
            self.ls.check_status("ls", "Login Server"),
            self.gs.check_status("gs", "Game Server"),
        ]
    }

    pub fn create_database(&self, db_id: &str) -> Result<usize, String> {
        match db_id {
            "cs" | "chat" => self.cs.create_database_and_tables("cs"),
            "ls" | "login" => self.ls.create_database_and_tables("ls"),
            _ => self.gs.create_database_and_tables("gs"),
        }
    }
}
