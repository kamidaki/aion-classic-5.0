use mysql::prelude::*;
use mysql::{OptsBuilder, Pool, Row};
use serde::{Deserialize, Serialize};
use serde_json::{Value};
use std::collections::HashMap;
use std::fs;
use std::sync::Arc;
use std::time::Instant;

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

#[derive(Clone)]
pub struct DbManager {
    pool: Option<Arc<Pool>>,
    pub db_name: String,
    pub host: String,
    pub port: u16,
    pub user: String,
}

impl DbManager {
    pub fn new() -> Self {
        let (host, port, user, pass, db_name) = Self::resolve_db_credentials();
        
        let pool = if !host.is_empty() && !user.is_empty() {
            let opts = OptsBuilder::new()
                .ip_or_hostname(Some(&host))
                .tcp_port(port)
                .user(Some(&user))
                .pass(Some(&pass))
                .db_name(Some(&db_name));
            
            Pool::new(opts).ok().map(Arc::new)
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

    fn resolve_db_credentials() -> (String, u16, String, String, String) {
        let prop_candidates = [
            "GameServer/config/network/database.properties",
            "LoginServer/config/network/database.properties",
            "../2 - Emulador [Produto Final]/GameServer/config/network/database.properties",
            "../2 - Emulador [Produto Final]/LoginServer/config/network/database.properties",
        ];

        for path_str in &prop_candidates {
            if let Ok(content) = fs::read_to_string(path_str) {
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

        ("127.0.0.1".to_string(), 3306, "root".to_string(), "".to_string(), "aiondbls_gs".to_string())
    }

    pub fn get_all_databases_schema(&self) -> Result<Vec<DatabaseGroup>, String> {
        let pool = match &self.pool {
            Some(p) => p,
            None => return Err("Conexão MySQL não configurada ou inativa.".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| format!("Erro MySQL: {}", e))?;

        let tables: Vec<String> = conn
            .query("SHOW TABLES")
            .map_err(|e| format!("Erro ao listar tabelas: {}", e))?;

        let mut table_schemas = Vec::new();
        let mut total_rows = 0i64;

        for table in &tables {
            let cols_query = format!("SHOW COLUMNS FROM `{}`", table);
            let cols_rows: Vec<Row> = conn.query(&cols_query).unwrap_or_default();

            let mut columns = Vec::new();
            for (idx, r) in cols_rows.iter().enumerate() {
                let col_name: String = r.get(0).unwrap_or_default();
                let type_name: String = r.get(1).unwrap_or_default();
                let null_str: String = r.get(2).unwrap_or_default();
                let key_str: String = r.get(3).unwrap_or_default();
                let dflt_val: Option<String> = r.get(4);

                columns.push(ColumnInfo {
                    cid: idx as i64,
                    name: col_name,
                    type_name,
                    notnull: null_str.to_uppercase() == "NO",
                    dflt_value: dflt_val,
                    pk: key_str.to_uppercase().contains("PRI"),
                });
            }

            let count_query = format!("SELECT COUNT(*) FROM `{}`", table);
            let row_count: i64 = conn.query_first(&count_query).unwrap_or(Some(0)).unwrap_or(0);
            total_rows += row_count;

            table_schemas.push(TableSchema {
                db_id: self.db_name.clone(),
                name: table.clone(),
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
            let col_name: String = r.get(0).unwrap_or_default();
            let type_name: String = r.get(1).unwrap_or_default();
            let null_str: String = r.get(2).unwrap_or_default();
            let key_str: String = r.get(3).unwrap_or_default();
            let dflt_val: Option<String> = r.get(4);
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
        let total_rows: i64 = conn.query_first(&count_query).unwrap_or(Some(0)).unwrap_or(0);

        let offset = page.saturating_sub(1) * limit;
        let data_query = format!("SELECT * FROM `{}` LIMIT {}, {}", table, offset, limit);
        let rows_data: Vec<Row> = conn.query(&data_query).map_err(|e| e.to_string())?;

        let mut rows = Vec::new();
        for r in rows_data {
            let mut row_map = HashMap::new();
            for (idx, col) in columns.iter().enumerate() {
                let val_str: Option<String> = r.get(idx);
                let json_val = match val_str {
                    Some(s) => Value::String(s),
                    None => Value::Null,
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
        conn.query_drop(format!("TRUNCATE TABLE `{}`", table)).map_err(|e| e.to_string())?;
        Ok(())
    }

    pub fn clean_all_tables(&self) -> Result<Vec<String>, String> {
        let pool = match &self.pool {
            Some(p) => p,
            None => return Err("Conexão MySQL inativa".to_string()),
        };

        let mut conn = pool.get_conn().map_err(|e| e.to_string())?;
        let tables: Vec<String> = conn.query("SHOW TABLES").map_err(|e| e.to_string())?;

        conn.query_drop("SET FOREIGN_KEY_CHECKS = 0").map_err(|e| e.to_string())?;
        for t in &tables {
            let _ = conn.query_drop(format!("TRUNCATE TABLE `{}`", t));
        }
        conn.query_drop("SET FOREIGN_KEY_CHECKS = 1").map_err(|e| e.to_string())?;
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
                    let s: Option<String> = r.get(idx);
                    row_vals.push(match s {
                        Some(val) => Value::String(val),
                        None => Value::Null,
                    });
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
                id: r.get(0).unwrap_or(0),
                name: r.get(1).unwrap_or_default(),
                account_name: r.get(2).unwrap_or_default(),
                class_name: r.get(3).unwrap_or_default(),
                race: r.get(4).unwrap_or_default(),
                exp: r.get(5).unwrap_or(0),
            });
        }
        list
    }
}
