use chrono::{Local, Utc};
use parking_lot::Mutex;
use serde::Serialize;
use std::collections::VecDeque;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::SystemTime;

#[derive(Debug, Clone, Serialize)]
pub struct LogEntry {
    pub id: u64,
    pub timestamp: String,
    pub server: String, // "login", "game", "chat"
    pub level: String,  // "INFO", "WARN", "ERROR", "DEBUG"
    pub message: String,
}

#[derive(Clone)]
pub struct LogCenter {
    entries: Arc<Mutex<VecDeque<LogEntry>>>,
    next_id: Arc<Mutex<u64>>,
    retention_days: u32,
    login_dir: PathBuf,
    game_dir: PathBuf,
    chat_dir: PathBuf,
}

impl LogCenter {
    pub fn new(retention_days: u32, login_path: &str, game_path: &str, chat_path: &str) -> Self {
        let login_dir = PathBuf::from(login_path);
        let game_dir = PathBuf::from(game_path);
        let chat_dir = PathBuf::from(chat_path);

        let _ = fs::create_dir_all(&login_dir);
        let _ = fs::create_dir_all(&game_dir);
        let _ = fs::create_dir_all(&chat_dir);

        let center = Self {
            entries: Arc::new(Mutex::new(VecDeque::with_capacity(1000))),
            next_id: Arc::new(Mutex::new(1)),
            retention_days,
            login_dir,
            game_dir,
            chat_dir,
        };

        center.cleanup_old_logs();
        center
    }

    pub fn push(&self, server: &str, raw_line: &str) {
        let trimmed = raw_line.trim();
        if trimmed.is_empty() {
            return;
        }

        let now_local = Local::now();
        let timestamp = now_local.format("%Y-%m-%d %H:%M:%S").to_string();
        let date_str = now_local.format("%Y-%m-%d").to_string();

        let level = if trimmed.contains("ERROR") || trimmed.contains("Fatal") || trimmed.contains("Panic") {
            "ERROR"
        } else if trimmed.contains("WARN") {
            "WARN"
        } else if trimmed.contains("DEBUG") {
            "DEBUG"
        } else {
            "INFO"
        };

        let mut id_lock = self.next_id.lock();
        let entry_id = *id_lock;
        *id_lock += 1;

        let entry = LogEntry {
            id: entry_id,
            timestamp: timestamp.clone(),
            server: server.to_string(),
            level: level.to_string(),
            message: trimmed.to_string(),
        };

        // In-memory buffer (capped at 500 entries)
        {
            let mut entries = self.entries.lock();
            if entries.len() >= 500 {
                entries.pop_front();
            }
            entries.push_back(entry);
        }

        // Write to daily physical log file
        let target_dir = match server {
            "login" => &self.login_dir,
            "game" => &self.game_dir,
            "chat" => &self.chat_dir,
            _ => &self.login_dir,
        };

        let log_file_path = target_dir.join(format!("{}.log", date_str));
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_file_path) {
            let log_line = format!("[{}] [{}] [{}] | {}\n", timestamp, level, server.to_uppercase(), trimmed);
            let _ = file.write_all(log_line.as_bytes());
        }
    }

    pub fn get_recent_entries(&self, limit: usize, filter_server: Option<&str>, filter_level: Option<&str>) -> Vec<LogEntry> {
        let entries = self.entries.lock();
        entries.iter()
            .filter(|e| {
                if let Some(srv) = filter_server {
                    if srv != "all" && e.server != srv {
                        return false;
                    }
                }
                if let Some(lvl) = filter_level {
                    if lvl != "all" && e.level != lvl {
                        return false;
                    }
                }
                true
            })
            .rev()
            .take(limit)
            .cloned()
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect()
    }

    pub fn cleanup_old_logs(&self) {
        let max_age_secs = (self.retention_days as u64) * 86400;
        let now = SystemTime::now();

        for dir in [&self.login_dir, &self.game_dir, &self.chat_dir] {
            if let Ok(entries) = fs::read_dir(dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.extension().and_then(|s| s.to_str()) == Some("log") {
                        if let Ok(meta) = entry.metadata() {
                            if let Ok(modified) = meta.modified() {
                                if let Ok(age) = now.duration_since(modified) {
                                    if age.as_secs() > max_age_secs {
                                        let _ = fs::remove_file(&path);
                                        println!("INFO: [LogCenter] Removed expired log file: {:?}", path);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
