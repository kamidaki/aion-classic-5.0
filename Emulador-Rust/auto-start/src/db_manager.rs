use rusqlite::{types::ValueRef, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

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

#[derive(Clone)]
pub struct DbManager {
    base_dir: PathBuf,
}

impl DbManager {
    pub fn new<P: AsRef<Path>>(path: P) -> Self {
        let base_path = path.as_ref();
        let base_dir = if base_path.is_file() {
            base_path.parent().unwrap_or(Path::new(".")).to_path_buf()
        } else {
            base_path.to_path_buf()
        };

        Self { base_dir }
    }

    fn resolve_db_path(&self, db_id: &str) -> PathBuf {
        let filename = match db_id.to_lowercase().as_str() {
            "login" | "login_db" | "login.db" => "login.db",
            "game" | "game_db" | "game.db" => "game.db",
            "chat" | "chat_db" | "chat.db" => "chat.db",
            _ => "login.db",
        };

        let candidates = [
            self.base_dir.join(filename),
            PathBuf::from("data/Banco de Dados").join(filename),
            PathBuf::from("../Produto Final/data/Banco de Dados").join(filename),
            PathBuf::from("Produto Final/data/Banco de Dados").join(filename),
            PathBuf::from("data").join(filename),
            PathBuf::from(filename),
        ];

        for c in &candidates {
            if c.exists() {
                return c.clone();
            }
        }

        candidates[0].clone()
    }

    pub fn get_conn_for(&self, db_id: &str) -> Result<Connection, String> {
        let path = self.resolve_db_path(db_id);
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        let conn = Connection::open(&path)
            .map_err(|e| format!("Erro ao abrir banco de dados '{}': {}", path.display(), e))?;

        let _ = conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA busy_timeout = 5000;
             PRAGMA synchronous = NORMAL;
             PRAGMA foreign_keys = OFF;",
        );

        Ok(conn)
    }

    fn find_db_for_table(&self, table: &str) -> String {
        for db_id in &["login", "game", "chat"] {
            if let Ok(conn) = self.get_conn_for(db_id) {
                let exists: bool = conn
                    .query_row(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = ?1",
                        [table],
                        |r| r.get::<_, i64>(0),
                    )
                    .map(|c| c > 0)
                    .unwrap_or(false);

                if exists {
                    return db_id.to_string();
                }
            }
        }
        "login".to_string()
    }

    pub fn get_all_databases_schema(&self) -> Result<Vec<DatabaseGroup>, String> {
        let targets = [
            ("login", "Login Server (login.db)", "login.db"),
            ("game", "Game Server (game.db)", "game.db"),
            ("chat", "Chat Server (chat.db)", "chat.db"),
        ];

        let mut groups = Vec::new();

        for (id, display_name, filename) in targets {
            let conn = match self.get_conn_for(id) {
                Ok(c) => c,
                Err(_) => continue,
            };

            let mut table_names: Vec<String> = Vec::new();
            if let Ok(mut stmt) = conn.prepare(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC",
            ) {
                if let Ok(rows) = stmt.query_map([], |row| row.get::<_, String>(0)) {
                    for r in rows.flatten() {
                        if !table_names.contains(&r) {
                            table_names.push(r);
                        }
                    }
                }
            }

            let mut tables = Vec::new();
            let mut total_rows = 0i64;

            for table in table_names {
                let row_count: i64 = conn
                    .query_row(&format!("SELECT COUNT(*) FROM \"{}\"", table), [], |r| {
                        r.get(0)
                    })
                    .unwrap_or(0);

                total_rows += row_count;

                let columns: Vec<ColumnInfo> = if let Ok(mut col_stmt) =
                    conn.prepare(&format!("PRAGMA table_info(\"{}\")", table))
                {
                    col_stmt
                        .query_map([], |row| {
                            Ok(ColumnInfo {
                                cid: row.get(0)?,
                                name: row.get(1)?,
                                type_name: row.get(2)?,
                                notnull: row.get::<_, i64>(3)? != 0,
                                dflt_value: row.get(4)?,
                                pk: row.get::<_, i64>(5)? != 0,
                            })
                        })
                        .ok()
                        .map(|iter| iter.filter_map(|r| r.ok()).collect())
                        .unwrap_or_default()
                } else {
                    Vec::new()
                };

                tables.push(TableSchema {
                    db_id: id.to_string(),
                    name: table,
                    row_count,
                    columns,
                });
            }

            groups.push(DatabaseGroup {
                id: id.to_string(),
                name: display_name.to_string(),
                filename: filename.to_string(),
                table_count: tables.len(),
                total_rows,
                tables,
            });
        }

        Ok(groups)
    }

    pub fn get_table_data(
        &self,
        db_id: Option<&str>,
        table: &str,
        page: usize,
        limit: usize,
        search: Option<&str>,
        sort_col: Option<&str>,
        sort_order: Option<&str>,
    ) -> Result<TableDataResult, String> {
        let active_db = db_id
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.find_db_for_table(table));

        let conn = self.get_conn_for(&active_db)?;

        // Validate table exists
        let exists: bool = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = ?1",
                [table],
                |r| r.get::<_, i64>(0),
            )
            .map(|c| c > 0)
            .unwrap_or(false);

        if !exists {
            return Err(format!(
                "Tabela '{}' não encontrada no banco de dados '{}'.",
                table, active_db
            ));
        }

        // Get table columns
        let mut col_stmt = conn
            .prepare(&format!("PRAGMA table_info(\"{}\")", table))
            .map_err(|e| e.to_string())?;

        let columns: Vec<ColumnInfo> = col_stmt
            .query_map([], |row| {
                Ok(ColumnInfo {
                    cid: row.get(0)?,
                    name: row.get(1)?,
                    type_name: row.get(2)?,
                    notnull: row.get::<_, i64>(3)? != 0,
                    dflt_value: row.get(4)?,
                    pk: row.get::<_, i64>(5)? != 0,
                })
            })
            .map_err(|e| e.to_string())?
            .filter_map(|r| r.ok())
            .collect();

        let pk_columns: Vec<String> = columns.iter().filter(|c| c.pk).map(|c| c.name.clone()).collect();

        let limit = if limit == 0 { 50 } else { limit.min(500) };
        let page = if page == 0 { 1 } else { page };
        let offset = (page - 1) * limit;

        // Build WHERE clause if search query is provided
        let mut where_clause = String::new();
        let mut search_param = String::new();
        let has_search = if let Some(s) = search {
            let trimmed = s.trim();
            if !trimmed.is_empty() {
                search_param = format!("%{}%", trimmed);
                let text_cols: Vec<String> = columns
                    .iter()
                    .map(|c| format!("CAST(\"{}\" AS TEXT) LIKE ?1", c.name))
                    .collect();
                if !text_cols.is_empty() {
                    where_clause = format!("WHERE {}", text_cols.join(" OR "));
                    true
                } else {
                    false
                }
            } else {
                false
            }
        } else {
            false
        };

        // Total rows count
        let count_sql = format!("SELECT COUNT(*) FROM \"{}\" {}", table, where_clause);
        let total_rows: i64 = if has_search {
            conn.query_row(&count_sql, [&search_param], |r| r.get(0))
                .unwrap_or(0)
        } else {
            conn.query_row(&count_sql, [], |r| r.get(0)).unwrap_or(0)
        };

        let total_pages = ((total_rows as f64) / (limit as f64)).ceil() as usize;

        // Sorting
        let mut order_clause = String::new();
        if let Some(sc) = sort_col {
            if columns.iter().any(|c| c.name.eq_ignore_ascii_case(sc)) {
                let order = if sort_order.unwrap_or("ASC").eq_ignore_ascii_case("DESC") {
                    "DESC"
                } else {
                    "ASC"
                };
                order_clause = format!("ORDER BY \"{}\" {}", sc, order);
            }
        } else if !pk_columns.is_empty() {
            order_clause = format!("ORDER BY \"{}\" ASC", pk_columns[0]);
        }

        let select_sql = format!(
            "SELECT * FROM \"{}\" {} {} LIMIT {} OFFSET {}",
            table, where_clause, order_clause, limit, offset
        );

        let mut stmt = conn.prepare(&select_sql).map_err(|e| e.to_string())?;
        let col_count = stmt.column_count();
        let col_names: Vec<String> = (0..col_count)
            .map(|i| stmt.column_name(i).unwrap().to_string())
            .collect();

        let row_mapper = |row: &rusqlite::Row| -> rusqlite::Result<HashMap<String, Value>> {
            let mut map = HashMap::new();
            for (idx, name) in col_names.iter().enumerate() {
                let val_ref = row.get_ref(idx)?;
                let json_val = match val_ref {
                    ValueRef::Null => Value::Null,
                    ValueRef::Integer(i) => json!(i),
                    ValueRef::Real(r) => json!(r),
                    ValueRef::Text(t) => json!(String::from_utf8_lossy(t)),
                    ValueRef::Blob(b) => {
                        json!(format!("[BLOB {} bytes]", b.len()))
                    }
                };
                map.insert(name.clone(), json_val);
            }
            Ok(map)
        };

        let rows: Vec<HashMap<String, Value>> = if has_search {
            stmt.query_map([&search_param], row_mapper)
                .map_err(|e| e.to_string())?
                .filter_map(|r| r.ok())
                .collect()
        } else {
            stmt.query_map([], row_mapper)
                .map_err(|e| e.to_string())?
                .filter_map(|r| r.ok())
                .collect()
        };

        Ok(TableDataResult {
            db_id: active_db,
            table: table.to_string(),
            columns,
            pk_columns,
            rows,
            total_rows,
            page,
            limit,
            total_pages: total_pages.max(1),
        })
    }

    pub fn insert_row(
        &self,
        db_id: Option<&str>,
        table: &str,
        data: &HashMap<String, Value>,
    ) -> Result<i64, String> {
        let active_db = db_id
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.find_db_for_table(table));

        let conn = self.get_conn_for(&active_db)?;

        if data.is_empty() {
            return Err("Nenhum dado fornecido para inserção.".to_string());
        }

        let keys: Vec<String> = data.keys().map(|k| format!("\"{}\"", k)).collect();
        let placeholders: Vec<String> = (1..=data.len()).map(|i| format!("?{}", i)).collect();
        let sql = format!(
            "INSERT INTO \"{}\" ({}) VALUES ({})",
            table,
            keys.join(", "),
            placeholders.join(", ")
        );

        let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
        let params: Vec<Box<dyn rusqlite::ToSql>> = data
            .values()
            .map(|v| -> Box<dyn rusqlite::ToSql> {
                match v {
                    Value::Null => Box::new(rusqlite::types::Null),
                    Value::Bool(b) => Box::new(*b as i64),
                    Value::Number(num) => {
                        if let Some(i) = num.as_i64() {
                            Box::new(i)
                        } else if let Some(f) = num.as_f64() {
                            Box::new(f)
                        } else {
                            Box::new(num.to_string())
                        }
                    }
                    Value::String(s) => Box::new(s.clone()),
                    _ => Box::new(v.to_string()),
                }
            })
            .collect();

        let params_slice: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
        stmt.execute(&*params_slice).map_err(|e| e.to_string())?;

        Ok(conn.last_insert_rowid())
    }

    pub fn update_row(
        &self,
        db_id: Option<&str>,
        table: &str,
        pk: &HashMap<String, Value>,
        updates: &HashMap<String, Value>,
    ) -> Result<usize, String> {
        let active_db = db_id
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.find_db_for_table(table));

        let conn = self.get_conn_for(&active_db)?;

        if updates.is_empty() {
            return Err("Nenhum campo informado para atualização.".to_string());
        }
        if pk.is_empty() {
            return Err("Chave primária não informada para atualização.".to_string());
        }

        let mut set_clauses = Vec::new();
        let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
        let mut idx = 1;

        for (col, val) in updates {
            set_clauses.push(format!("\"{}\" = ?{}", col, idx));
            idx += 1;
            params.push(Self::json_to_tosql(val));
        }

        let mut where_clauses = Vec::new();
        for (pk_col, pk_val) in pk {
            where_clauses.push(format!("\"{}\" = ?{}", pk_col, idx));
            idx += 1;
            params.push(Self::json_to_tosql(pk_val));
        }

        let sql = format!(
            "UPDATE \"{}\" SET {} WHERE {}",
            table,
            set_clauses.join(", "),
            where_clauses.join(" AND ")
        );

        let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
        let params_slice: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
        let rows_affected = stmt.execute(&*params_slice).map_err(|e| e.to_string())?;

        Ok(rows_affected)
    }

    pub fn delete_row(
        &self,
        db_id: Option<&str>,
        table: &str,
        pk: &HashMap<String, Value>,
    ) -> Result<usize, String> {
        let active_db = db_id
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.find_db_for_table(table));

        let conn = self.get_conn_for(&active_db)?;

        if pk.is_empty() {
            return Err("Chave primária não informada para exclusão.".to_string());
        }

        let mut where_clauses = Vec::new();
        let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
        let mut idx = 1;

        for (pk_col, pk_val) in pk {
            where_clauses.push(format!("\"{}\" = ?{}", pk_col, idx));
            idx += 1;
            params.push(Self::json_to_tosql(pk_val));
        }

        let sql = format!("DELETE FROM \"{}\" WHERE {}", table, where_clauses.join(" AND "));
        let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
        let params_slice: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
        let rows_affected = stmt.execute(&*params_slice).map_err(|e| e.to_string())?;

        Ok(rows_affected)
    }

    pub fn truncate_table(&self, db_id: Option<&str>, table: &str) -> Result<(), String> {
        let active_db = db_id
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| self.find_db_for_table(table));

        let conn = self.get_conn_for(&active_db)?;

        let _ = conn.execute(&format!("DELETE FROM \"{}\"", table), []);
        let _ = conn.execute("DELETE FROM sqlite_sequence WHERE name = ?1", [table]);
        let _ = conn.execute("VACUUM", []);

        Ok(())
    }

    pub fn clean_all_tables(&self) -> Result<Vec<String>, String> {
        let mut cleaned = Vec::new();
        for db_id in &["login", "game", "chat"] {
            if let Ok(conn) = self.get_conn_for(db_id) {
                if let Ok(mut stmt) = conn.prepare(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                ) {
                    if let Ok(rows) = stmt.query_map([], |r| r.get::<_, String>(0)) {
                        for t in rows.flatten() {
                            let _ = conn.execute(&format!("DELETE FROM \"{}\"", t), []);
                            cleaned.push(format!("{}/{}", db_id, t));
                        }
                    }
                }
                let _ = conn.execute("DELETE FROM sqlite_sequence", []);
                let _ = conn.execute("VACUUM", []);
            }
        }
        Ok(cleaned)
    }

    pub fn execute_query(&self, db_id: Option<&str>, sql: &str) -> Result<QueryResult, String> {
        let active_db = db_id.unwrap_or("game");
        let conn = self.get_conn_for(active_db)?;

        let start = std::time::Instant::now();
        let trimmed = sql.trim();
        let is_select = trimmed.to_uppercase().starts_with("SELECT")
            || trimmed.to_uppercase().starts_with("PRAGMA")
            || trimmed.to_uppercase().starts_with("EXPLAIN");

        if is_select {
            let mut stmt = conn.prepare(trimmed).map_err(|e| e.to_string())?;
            let col_count = stmt.column_count();
            let columns: Vec<String> = (0..col_count)
                .map(|i| stmt.column_name(i).unwrap().to_string())
                .collect();

            let rows_result: rusqlite::Result<Vec<Vec<Value>>> = stmt
                .query_map([], |row| {
                    let mut row_vals = Vec::new();
                    for idx in 0..col_count {
                        let val_ref = row.get_ref(idx)?;
                        let val = match val_ref {
                            ValueRef::Null => Value::Null,
                            ValueRef::Integer(i) => json!(i),
                            ValueRef::Real(r) => json!(r),
                            ValueRef::Text(t) => json!(String::from_utf8_lossy(t)),
                            ValueRef::Blob(b) => json!(format!("[BLOB {} bytes]", b.len())),
                        };
                        row_vals.push(val);
                    }
                    Ok(row_vals)
                })
                .map_err(|e| e.to_string())?
                .collect();

            let elapsed = start.elapsed().as_secs_f64() * 1000.0;
            let rows = rows_result.map_err(|e| e.to_string())?;

            Ok(QueryResult {
                is_select: true,
                columns,
                rows,
                affected_rows: 0,
                execution_time_ms: elapsed,
                error: None,
            })
        } else {
            let affected = conn.execute_batch(trimmed).map_err(|e| e.to_string())?;
            let elapsed = start.elapsed().as_secs_f64() * 1000.0;

            Ok(QueryResult {
                is_select: false,
                columns: Vec::new(),
                rows: Vec::new(),
                affected_rows: 1,
                execution_time_ms: elapsed,
                error: None,
            })
        }
    }

    fn json_to_tosql(v: &Value) -> Box<dyn rusqlite::ToSql> {
        match v {
            Value::Null => Box::new(rusqlite::types::Null),
            Value::Bool(b) => Box::new(*b as i64),
            Value::Number(num) => {
                if let Some(i) = num.as_i64() {
                    Box::new(i)
                } else if let Some(f) = num.as_f64() {
                    Box::new(f)
                } else {
                    Box::new(num.to_string())
                }
            }
            Value::String(s) => Box::new(s.clone()),
            _ => Box::new(v.to_string()),
        }
    }
}
