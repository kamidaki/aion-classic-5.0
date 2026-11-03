use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertiesFileInfo {
    pub server_id: String,
    pub server_label: String,
    pub name: String,
    pub rel_path: String,
    pub full_path: String,
    pub category: String,
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyItem {
    pub key: String,
    pub value: String,
    pub comment: Option<String>,
    pub category: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertiesFileContent {
    pub rel_path: String,
    pub full_path: String,
    pub server_id: String,
    pub items: Vec<PropertyItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SaveResult {
    pub backup_path: String,
    pub saved_keys_count: usize,
    pub message: String,
}

pub struct PropertiesManager;

impl PropertiesManager {
    /// Categorizes a property key into a logical group
    pub fn categorize_key(key: &str) -> String {
        let k = key.to_lowercase();
        if k.contains("socket") || k.contains("port") || k.contains("ip") || k.contains("address") || k.contains("nio") || k.contains("flood") || k.contains("network") {
            "Network".to_string()
        } else if k.contains("database") || k.contains("jdbc") || k.contains("connectionpool") || k.contains("sql") {
            "Database".to_string()
        } else if k.contains("thread") || k.contains("processor") || k.contains("pool") || k.contains("memory") || k.contains("cleaning") || k.contains("periodicsave") {
            "Performance".to_string()
        } else if k.contains("rate") || k.contains("exp") || k.contains("drop") || k.contains("quest") || k.contains("craft") || k.contains("pvp") || k.contains("siege") || k.contains("ranking") {
            "Rates & Rewards".to_string()
        } else if k.contains("security") || k.contains("ban") || k.contains("admin") || k.contains("punishment") || k.contains("accesslevel") || k.contains("password") {
            "Security & Admin".to_string()
        } else if k.contains("housing") || k.contains("instance") || k.contains("legion") || k.contains("trade") || k.contains("world") || k.contains("ai") || k.contains("event") {
            "Gameplay & World".to_string()
        } else {
            "General".to_string()
        }
    }

    /// Lists all .properties files for active and known servers
    pub fn list_files(servers: &HashMap<String, crate::config::ServerConfig>) -> Vec<PropertiesFileInfo> {
        let mut list = Vec::new();

        for (srv_id, cfg) in servers {
            let working_dir = if cfg.working_dir.is_empty() {
                PathBuf::from(".")
            } else {
                PathBuf::from(&cfg.working_dir)
            };

            let config_dir = working_dir.join("config");
            if !config_dir.exists() {
                continue;
            }

            Self::scan_properties_dir(&config_dir, srv_id, &cfg.label, &mut list);
        }

        // Sort by server_id then by name
        list.sort_by(|a, b| a.server_id.cmp(&b.server_id).then(a.name.cmp(&b.name)));
        list
    }

    fn scan_properties_dir(dir: &Path, srv_id: &str, srv_label: &str, out: &mut Vec<PropertiesFileInfo>) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    Self::scan_properties_dir(&p, srv_id, srv_label, out);
                } else if p.extension().map_or(false, |ext| ext == "properties") {
                    let name = p.file_name().unwrap_or_default().to_string_lossy().to_string();
                    let full_path = p.to_string_lossy().to_string();
                    let metadata = p.metadata().ok();
                    let size_bytes = metadata.map(|m| m.len()).unwrap_or(0);
                    
                    let category = if full_path.contains("network") {
                        "Network".to_string()
                    } else if full_path.contains("administration") {
                        "Administration".to_string()
                    } else {
                        "Main Configuration".to_string()
                    };

                    out.push(PropertiesFileInfo {
                        server_id: srv_id.to_string(),
                        server_label: srv_label.to_string(),
                        name,
                        rel_path: full_path.clone(),
                        full_path,
                        category,
                        size_bytes,
                    });
                }
            }
        }
    }

    /// Reads and parses a properties file
    pub fn read_file(path_str: &str, server_id: Option<&str>) -> Result<PropertiesFileContent, String> {
        let p = Path::new(path_str);
        if !p.exists() {
            return Err(format!("Arquivo properties não encontrado: {}", path_str));
        }

        let content = fs::read_to_string(p).map_err(|e| format!("Erro ao ler arquivo: {}", e))?;
        let mut items = Vec::new();
        let mut pending_comment = Vec::new();

        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                pending_comment.clear();
                continue;
            }

            if trimmed.starts_with('#') || trimmed.starts_with('!') {
                let comment_text = trimmed.trim_start_matches(['#', '!', ' ']).trim();
                if !comment_text.is_empty() {
                    pending_comment.push(comment_text.to_string());
                }
                continue;
            }

            if let Some((k, v)) = trimmed.split_once('=') {
                let key = k.trim().to_string();
                let value = v.trim().to_string();
                let comment = if !pending_comment.is_empty() {
                    Some(pending_comment.join("\n"))
                } else {
                    None
                };
                let category = Self::categorize_key(&key);

                items.push(PropertyItem {
                    key,
                    value,
                    comment,
                    category,
                });
                pending_comment.clear();
            }
        }

        Ok(PropertiesFileContent {
            rel_path: path_str.to_string(),
            full_path: p.canonicalize().unwrap_or_else(|_| p.to_path_buf()).to_string_lossy().to_string(),
            server_id: server_id.unwrap_or("unknown").to_string(),
            items,
        })
    }

    /// Saves updated property values while preserving comments and creating a timestamped backup
    pub fn save_file(path_str: &str, updates: &HashMap<String, String>) -> Result<SaveResult, String> {
        let p = Path::new(path_str);
        if !p.exists() {
            return Err(format!("Arquivo properties não encontrado para salvar: {}", path_str));
        }

        let original_content = fs::read_to_string(p).map_err(|e| format!("Erro ao ler original: {}", e))?;

        // 1. Create timestamped backup (.bak)
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let backup_path = format!("{}.{}.bak", path_str, timestamp);
        fs::write(&backup_path, &original_content).map_err(|e| format!("Falha ao criar backup: {}", e))?;

        // 2. Build modified content line by line preserving comments
        let mut new_lines = Vec::new();
        let mut saved_keys = 0;
        let mut modified_keys = std::collections::HashSet::new();

        for line in original_content.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with('#') || trimmed.starts_with('!') || !trimmed.contains('=') {
                new_lines.push(line.to_string());
                continue;
            }

            if let Some((k, _)) = trimmed.split_once('=') {
                let key = k.trim();
                if let Some(new_val) = updates.get(key) {
                    new_lines.push(format!("{} = {}", key, new_val));
                    saved_keys += 1;
                    modified_keys.insert(key.to_string());
                } else {
                    new_lines.push(line.to_string());
                }
            } else {
                new_lines.push(line.to_string());
            }
        }

        // 3. Append any newly added keys not in original file
        for (k, v) in updates {
            if !modified_keys.contains(k) {
                new_lines.push(format!("{} = {}", k, v));
                saved_keys += 1;
            }
        }

        let result_content = new_lines.join("\r\n");
        fs::write(p, result_content).map_err(|e| format!("Erro ao gravar arquivo properties: {}", e))?;

        Ok(SaveResult {
            backup_path,
            saved_keys_count: saved_keys,
            message: format!("Arquivo salvo com sucesso! {} propriedades atualizadas.", saved_keys),
        })
    }
}

