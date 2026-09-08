use chrono::Local;
use parking_lot::Mutex;
use serde::Serialize;
use std::collections::VecDeque;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
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

fn strip_ansi(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let chars: Vec<char> = input.chars().collect();
    let len = chars.len();
    let mut i = 0;
    while i < len {
        if chars[i] == '\x1b' {
            i += 1;
            if i < len && chars[i] == '[' {
                i += 1;
                while i < len {
                    let c = chars[i];
                    if c >= '@' && c <= '~' {
                        i += 1;
                        break;
                    }
                    i += 1;
                }
            }
            continue;
        }
        out.push(chars[i]);
        i += 1;
    }
    out
}

pub fn clean_log_line(raw: &str) -> (String, String) {
    let unescaped = strip_ansi(raw);
    let mut trimmed = unescaped.trim();
    if trimmed.is_empty() {
        return ("INFO".to_string(), String::new());
    }

    let mut level = "INFO".to_string();

    // 1. If line starts with ISO date or time (HH:mm:ss)
    if trimmed.len() >= 8 {
        let b = trimmed.as_bytes();
        if b[2] == b':' && b[5] == b':' && b[0].is_ascii_digit() && b[1].is_ascii_digit() && b[3].is_ascii_digit() && b[4].is_ascii_digit() {
            trimmed = trimmed[8..].trim_start();
            if trimmed.starts_with('.') || trimmed.starts_with(',') {
                if let Some(idx) = trimmed.find(' ') {
                    trimmed = trimmed[idx..].trim_start();
                }
            }
        } else if trimmed.len() >= 19 && b[4] == b'-' && b[7] == b'-' {
            if let Some(idx) = trimmed.find(' ') {
                trimmed = trimmed[idx..].trim_start();
            }
        }
    }

    // 2. Check for log level at start (INFO, WARN, WARNING, ERROR, DEBUG, TRACE, FATAL)
    let upper = trimmed.to_uppercase();
    if upper.starts_with("INFO") {
        level = "INFO".to_string();
        trimmed = trimmed[4..].trim_start();
    } else if upper.starts_with("WARN") {
        level = "WARN".to_string();
        if upper.starts_with("WARNING") {
            trimmed = trimmed[7..].trim_start();
        } else {
            trimmed = trimmed[4..].trim_start();
        }
    } else if upper.starts_with("ERROR") {
        level = "ERROR".to_string();
        trimmed = trimmed[5..].trim_start();
    } else if upper.starts_with("DEBUG") {
        level = "DEBUG".to_string();
        trimmed = trimmed[5..].trim_start();
    } else if upper.starts_with("TRACE") {
        level = "DEBUG".to_string();
        trimmed = trimmed[5..].trim_start();
    } else if upper.starts_with("FATAL") {
        level = "ERROR".to_string();
        trimmed = trimmed[5..].trim_start();
    }

    // 3. Skip thread indicator e.g. [main] or [pool-1-thread-1]
    if trimmed.starts_with('[') {
        if let Some(end_bracket) = trimmed.find(']') {
            let inside = &trimmed[1..end_bracket];
            if inside.eq_ignore_ascii_case("main") || inside.contains("thread") || inside.contains("pool") || inside.contains("Dispatcher") {
                trimmed = trimmed[end_bracket + 1..].trim_start();
            }
        }
    }

    // 4. Strip logger package prefix if followed by " - " (e.g. com.aionemu... - Message)
    if let Some(dash_idx) = trimmed.find(" - ") {
        let prefix = &trimmed[..dash_idx];
        if prefix.contains("com.") || prefix.contains("org.") || prefix.contains("ch.qos") || prefix.contains('.') || prefix.contains("Config") || prefix.contains("Service") {
            trimmed = trimmed[dash_idx + 3..].trim_start();
        } else if dash_idx == 0 {
            trimmed = trimmed[3..].trim_start();
        }
    } else if trimmed.starts_with("- ") {
        trimmed = trimmed[2..].trim_start();
    }

    // 5. If level is still INFO, detect from keyword in raw line
    if level == "INFO" {
        if unescaped.contains("ERROR") || unescaped.contains("Exception") || unescaped.contains("Error") || unescaped.contains("Falha") || unescaped.contains("Fatal") {
            level = "ERROR".to_string();
        } else if unescaped.contains("WARN") || unescaped.contains("Aviso") {
            level = "WARN".to_string();
        } else if unescaped.contains("DEBUG") {
            level = "DEBUG".to_string();
        }
    }

    let final_msg = if trimmed.is_empty() { unescaped.trim().to_string() } else { trimmed.to_string() };
    (level, final_msg)
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
        let (level, clean_message) = clean_log_line(raw_line);
        if clean_message.trim().is_empty() {
            return;
        }

        let now_local = Local::now();
        let timestamp = now_local.format("%Y-%m-%d %H:%M:%S").to_string();
        let date_str = now_local.format("%Y-%m-%d").to_string();

        let mut id_lock = self.next_id.lock();
        let entry_id = *id_lock;
        *id_lock += 1;

        let entry = LogEntry {
            id: entry_id,
            timestamp: timestamp.clone(),
            server: server.to_string(),
            level: level.clone(),
            message: clean_message.clone(),
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
            let log_line = format!("[{}] {} - {}: {}\n", timestamp, server.to_uppercase(), level, clean_message);
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
