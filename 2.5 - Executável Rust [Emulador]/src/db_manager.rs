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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewColumnDef {
    pub name: String,
    pub type_name: String,
    pub pk: bool,
    pub notnull: bool,
    pub dflt_value: Option<String>,
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

    pub fn get_storage_dir(&self) -> PathBuf {
        let candidates = [
            self.base_dir.clone(),
            PathBuf::from("data/server/Banco de Dados"),
            PathBuf::from("../Produto Final/data/server/Banco de Dados"),
            PathBuf::from("Produto Final/data/server/Banco de Dados"),
            PathBuf::from("data/Banco de Dados"),
            PathBuf::from("../Produto Final/data/Banco de Dados"),
            PathBuf::from("Produto Final/data/Banco de Dados"),
            PathBuf::from("data"),
            PathBuf::from("."),
        ];

        for c in &candidates {
            if c.exists() && c.is_dir() {
                return c.clone();
            }
        }

        let default_dir = PathBuf::from("data/server/Banco de Dados");
        let _ = std::fs::create_dir_all(&default_dir);
        default_dir
    }

    pub fn resolve_db_path(&self, db_id: &str) -> PathBuf {
        let clean_id = db_id.trim();
        let filename = if clean_id.to_lowercase().ends_with(".db") {
            clean_id.to_string()
        } else {
            match clean_id.to_lowercase().as_str() {
                "login" | "login_db" => "login.db".to_string(),
                "game" | "game_db" => "game.db".to_string(),
                "chat" | "chat_db" => "chat.db".to_string(),
                other => format!("{}.db", other),
            }
        };

        let candidates = [
            self.base_dir.join(&filename),
            PathBuf::from("data/server/Banco de Dados").join(&filename),
            PathBuf::from("../Produto Final/data/server/Banco de Dados").join(&filename),
            PathBuf::from("Produto Final/data/server/Banco de Dados").join(&filename),
            PathBuf::from("data/Banco de Dados").join(&filename),
            PathBuf::from("../Produto Final/data/Banco de Dados").join(&filename),
            PathBuf::from("Produto Final/data/Banco de Dados").join(&filename),
            PathBuf::from("data").join(&filename),
            PathBuf::from(&filename),
        ];

        for c in &candidates {
            if c.exists() {
                return c.clone();
            }
        }

        self.get_storage_dir().join(&filename)
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

    pub fn find_db_for_table(&self, table: &str) -> String {
        if let Ok(schemas) = self.get_all_databases_schema() {
            for group in schemas {
                if group.tables.iter().any(|t| t.name.eq_ignore_ascii_case(table)) {
                    return group.id;
                }
            }
        }
        "game".to_string()
    }

    pub fn get_all_databases_schema(&self) -> Result<Vec<DatabaseGroup>, String> {
        let mut db_map: HashMap<String, (String, PathBuf)> = HashMap::new();

        // 1. Core predefined databases
        db_map.insert("login".to_string(), ("Login Server (login.db)".to_string(), self.resolve_db_path("login.db")));
        db_map.insert("game".to_string(), ("Game Server (game.db)".to_string(), self.resolve_db_path("game.db")));
        db_map.insert("chat".to_string(), ("Chat Server (chat.db)".to_string(), self.resolve_db_path("chat.db")));

        // 2. Discover all other .db files in active folders
        let search_dirs = [
            self.get_storage_dir(),
            self.base_dir.clone(),
            PathBuf::from("data/server/Banco de Dados"),
            PathBuf::from("Produto Final/data/server/Banco de Dados"),
            PathBuf::from("data/Banco de Dados"),
            PathBuf::from("Produto Final/data/Banco de Dados"),
            PathBuf::from("data"),
            PathBuf::from("."),
        ];

        for dir in &search_dirs {
            if let Ok(entries) = std::fs::read_dir(dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_file() {
                        if let Some(ext) = path.extension() {
                            if ext.eq_ignore_ascii_case("db") {
                                if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                                    let id = stem.to_lowercase();
                                    if !db_map.contains_key(&id) && !id.starts_with("declarative_") && !id.starts_with("thumbs") && !id.starts_with("cache") {
                                        let name = format!("{} ({}.db)", stem, stem);
                                        db_map.insert(id, (name, path.clone()));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Sort: login first, game second, chat third, then alphabetical
        let mut sorted_keys: Vec<String> = db_map.keys().cloned().collect();
        sorted_keys.sort_by(|a, b| {
            let order = |k: &str| match k {
                "login" => 1,
                "game" => 2,
                "chat" => 3,
                "aion" => 4,
                _ => 10,
            };
            order(a).cmp(&order(b)).then_with(|| a.cmp(b))
        });

        let mut groups = Vec::new();

        for id in sorted_keys {
            let (display_name, path) = match db_map.get(&id) {
                Some(v) => v,
                None => continue,
            };

            let filename = path.file_name().and_then(|f| f.to_str()).unwrap_or("database.db").to_string();
            let size_bytes = std::fs::metadata(path).map(|m| m.len()).unwrap_or(0);

            let conn = match Connection::open(path) {
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
                    db_id: id.clone(),
                    name: table,
                    row_count,
                    columns,
                });
            }

            groups.push(DatabaseGroup {
                id: id.clone(),
                name: display_name.clone(),
                filename,
                size_bytes,
                table_count: tables.len(),
                total_rows,
                tables,
            });
        }

        Ok(groups)
    }

    pub fn create_database(&self, name: &str) -> Result<String, String> {
        let clean_name = name.trim().replace(|c: char| !c.is_alphanumeric() && c != '_' && c != '-', "");
        if clean_name.is_empty() {
            return Err("Nome de banco de dados inválido.".to_string());
        }

        let filename = format!("{}.db", clean_name);
        let storage_dir = self.get_storage_dir();
        let path = storage_dir.join(&filename);

        if path.exists() {
            return Err(format!("Banco de dados '{}' já existe.", filename));
        }

        let conn = Connection::open(&path)
            .map_err(|e| format!("Falha ao criar banco de dados '{}': {}", path.display(), e))?;

        let _ = conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;
             CREATE TABLE IF NOT EXISTS _schema_info (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                 version TEXT DEFAULT '1.0'
             );",
        );

        Ok(clean_name)
    }

    pub fn delete_database(&self, db_id: &str) -> Result<(), String> {
        let clean_id = db_id.trim().to_lowercase();
        if clean_id == "login" || clean_id == "game" || clean_id == "chat" {
            return Err("Não é permitido excluir os bancos de dados do núcleo do servidor (login, game, chat).".to_string());
        }

        let path = self.resolve_db_path(&clean_id);
        if !path.exists() {
            return Err(format!("Banco de dados '{}' não encontrado.", db_id));
        }

        // Delete .db, .db-wal, .db-shm
        let _ = std::fs::remove_file(&path);
        let wal_path = PathBuf::from(format!("{}-wal", path.display()));
        if wal_path.exists() {
            let _ = std::fs::remove_file(wal_path);
        }
        let shm_path = PathBuf::from(format!("{}-shm", path.display()));
        if shm_path.exists() {
            let _ = std::fs::remove_file(shm_path);
        }

        Ok(())
    }

    pub fn create_table(
        &self,
        db_id: &str,
        table_name: &str,
        columns: &[NewColumnDef],
    ) -> Result<(), String> {
        let clean_table = table_name.trim().replace(|c: char| !c.is_alphanumeric() && c != '_', "");
        if clean_table.is_empty() {
            return Err("Nome de tabela inválido.".to_string());
        }
        if columns.is_empty() {
            return Err("A tabela deve conter ao menos uma coluna.".to_string());
        }

        let conn = self.get_conn_for(db_id)?;

        let mut col_defs = Vec::new();
        let mut pk_cols = Vec::new();

        for col in columns {
            let c_name = col.name.trim().replace(|c: char| !c.is_alphanumeric() && c != '_', "");
            if c_name.is_empty() {
                continue;
            }
            let c_type = match col.type_name.to_uppercase().as_str() {
                "INTEGER" | "INT" => "INTEGER",
                "REAL" | "FLOAT" | "DOUBLE" => "REAL",
                "BLOB" => "BLOB",
                _ => "TEXT",
            };

            let mut def = format!("\"{}\" {}", c_name, c_type);
            if col.notnull {
                def.push_str(" NOT NULL");
            }
            if let Some(ref dflt) = col.dflt_value {
                if !dflt.trim().is_empty() {
                    def.push_str(&format!(" DEFAULT '{}'", dflt.replace('\'', "''")));
                }
            }
            col_defs.push(def);

            if col.pk {
                pk_cols.push(format!("\"{}\"", c_name));
            }
        }

        if !pk_cols.is_empty() {
            col_defs.push(format!("PRIMARY KEY ({})", pk_cols.join(", ")));
        }

        let create_sql = format!(
            "CREATE TABLE \"{}\" (\n    {}\n);",
            clean_table,
            col_defs.join(",\n    ")
        );

        conn.execute(&create_sql, [])
            .map_err(|e| format!("Erro ao criar tabela '{}': {}", clean_table, e))?;

        Ok(())
    }

    pub fn drop_table(&self, db_id: &str, table_name: &str) -> Result<(), String> {
        let clean_table = table_name.trim();
        if clean_table.is_empty() {
            return Err("Nome de tabela inválido.".to_string());
        }

        let conn = self.get_conn_for(db_id)?;
        conn.execute(&format!("DROP TABLE IF EXISTS \"{}\"", clean_table), [])
            .map_err(|e| format!("Erro ao remover tabela '{}': {}", clean_table, e))?;

        let _ = conn.execute("VACUUM", []);
        Ok(())
    }

    pub fn add_column(
        &self,
        db_id: &str,
        table_name: &str,
        col: &NewColumnDef,
    ) -> Result<(), String> {
        let clean_table = table_name.trim();
        let c_name = col.name.trim().replace(|c: char| !c.is_alphanumeric() && c != '_', "");
        if c_name.is_empty() {
            return Err("Nome da coluna inválido.".to_string());
        }

        let c_type = match col.type_name.to_uppercase().as_str() {
            "INTEGER" | "INT" => "INTEGER",
            "REAL" | "FLOAT" | "DOUBLE" => "REAL",
            "BLOB" => "BLOB",
            _ => "TEXT",
        };

        let mut sql = format!("ALTER TABLE \"{}\" ADD COLUMN \"{}\" {}", clean_table, c_name, c_type);
        if col.notnull {
            sql.push_str(" NOT NULL");
        }
        if let Some(ref dflt) = col.dflt_value {
            if !dflt.trim().is_empty() {
                sql.push_str(&format!(" DEFAULT '{}'", dflt.replace('\'', "''")));
            } else if col.notnull {
                sql.push_str(" DEFAULT ''");
            }
        }

        let conn = self.get_conn_for(db_id)?;
        conn.execute(&sql, [])
            .map_err(|e| format!("Erro ao adicionar coluna: {}", e))?;

        Ok(())
    }

    pub fn rename_table(
        &self,
        db_id: &str,
        old_name: &str,
        new_name: &str,
    ) -> Result<(), String> {
        let clean_old = old_name.trim();
        let clean_new = new_name.trim().replace(|c: char| !c.is_alphanumeric() && c != '_', "");
        if clean_new.is_empty() {
            return Err("Novo nome de tabela inválido.".to_string());
        }

        let conn = self.get_conn_for(db_id)?;
        let sql = format!("ALTER TABLE \"{}\" RENAME TO \"{}\"", clean_old, clean_new);
        conn.execute(&sql, [])
            .map_err(|e| format!("Erro ao renomear tabela: {}", e))?;

        Ok(())
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
        if let Ok(schemas) = self.get_all_databases_schema() {
            for db in schemas {
                if let Ok(conn) = self.get_conn_for(&db.id) {
                    for t in db.tables {
                        let _ = conn.execute(&format!("DELETE FROM \"{}\"", t.name), []);
                        cleaned.push(format!("{}/{}", db.id, t.name));
                    }
                    let _ = conn.execute("DELETE FROM sqlite_sequence", []);
                    let _ = conn.execute("VACUUM", []);
                }
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
            conn.execute_batch(trimmed).map_err(|e| e.to_string())?;
            let elapsed = start.elapsed().as_secs_f64() * 1000.0;

            Ok(QueryResult {
                is_select: false,
                columns: Vec::new(),
                rows: Vec::new(),
                affected_rows: conn.changes() as usize,
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
