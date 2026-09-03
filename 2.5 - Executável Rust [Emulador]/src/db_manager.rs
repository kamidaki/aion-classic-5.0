use mysql::prelude::*;
use mysql::{OptsBuilder, Pool, Row};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Instant;
use crate::config::DatabaseSettings;

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
    pool: Option<Arc<Pool>>,
    pub db_name: String,
    pub host: String,
    pub port: u16,
    pub user: String,
}

impl DbManager {
    pub fn new(cfg_db: &DatabaseSettings) -> Self {
        let (host, port, user, pass, db_name) = Self::resolve_db_credentials(cfg_db);
        
        let pool = if !host.is_empty() && !user.is_empty() {
            let opts = OptsBuilder::new()
                .ip_or_hostname(Some(&host))
                .tcp_port(port)
                .user(Some(&user))
                .pass(Some(&pass))
                .db_name(Some(&db_name))
                .prefer_socket(false);
            
            match Pool::new(opts) {
                Ok(p) => {
                    match p.get_conn() {
                        Ok(_) => {
                            eprintln!("[DbManager] Conectado com sucesso ao MySQL em {}:{}/{}", host, port, db_name);
                            Some(Arc::new(p))
                        }
                        Err(e) => {
                            eprintln!("[DbManager] Erro de autenticação/conexão MySQL {}:{}: {}", host, port, e);
                            None
                        }
                    }
                }
                Err(e) => {
                    eprintln!("[DbManager] Erro ao criar pool MySQL {}:{}: {}", host, port, e);
                    None
                }
            }
        } else {
            None
        };

        Self {
            pool,
            db_name,
            host,
            port,
            user,
        }
    }

    fn resolve_db_credentials(cfg_db: &DatabaseSettings) -> (String, u16, String, String, String) {
        // 1. If explicit credentials provided in config.json and not auto_read, use them
        if !cfg_db.auto_read_properties && !cfg_db.host.is_empty() && !cfg_db.user.is_empty() {
            return (
                cfg_db.host.clone(),
                cfg_db.port,
                cfg_db.user.clone(),
                cfg_db.password.clone(),
                cfg_db.database.clone(),
            );
        }

        // 2. Search database.properties in all candidate directories
        let mut candidates = Vec::new();
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                candidates.push(exe_dir.join("GameServer/config/network/database.properties"));
                candidates.push(exe_dir.join("LoginServer/config/network/database.properties"));
                candidates.push(exe_dir.join("../2 - Emulador [Produto Final]/GameServer/config/network/database.properties"));
                candidates.push(exe_dir.join("../1 - Código Fonte [Emulador]/GameServer/config/network/database.properties"));
            }
        }
        candidates.push(PathBuf::from("GameServer/config/network/database.properties"));
        candidates.push(PathBuf::from("LoginServer/config/network/database.properties"));
        candidates.push(PathBuf::from("2 - Emulador [Produto Final]/GameServer/config/network/database.properties"));
        candidates.push(PathBuf::from("1 - Código Fonte [Emulador]/GameServer/config/network/database.properties"));

        for p in &candidates {
            if let Ok(content) = fs::read_to_string(p) {
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
                    let mut db = "aiondbls_gs".to_string();

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
            }
        }

        // 3. Fallback to cfg_db if available
        if !cfg_db.host.is_empty() && !cfg_db.user.is_empty() {
            return (
                cfg_db.host.clone(),
                cfg_db.port,
                cfg_db.user.clone(),
                cfg_db.password.clone(),
                cfg_db.database.clone(),
            );
        }

        ("192.168.3.29".to_string(), 3310, "aionliveclassic".to_string(), "@d@mn0gu31r4".to_string(), "aiondbls_gs".to_string())
    }

    pub fn get_summary(&self) -> (bool, usize, i64) {
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
        let pool = match &self.pool {
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
