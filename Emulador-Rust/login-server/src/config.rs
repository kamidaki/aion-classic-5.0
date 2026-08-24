use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct SecurityConfig {
    #[serde(default = "default_true")]
    pub enable_rate_limit: bool,
    #[serde(default = "default_max_attempts")]
    pub max_attempts_per_minute: u32,
    #[serde(default = "default_ban_minutes")]
    pub temp_ban_minutes: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    #[serde(default = "default_db_path")]
    pub path: String,
}

#[derive(Debug, Deserialize, Clone)]
pub struct LoginServerConfig {
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default = "default_bind")]
    pub bind_address: String,
    #[serde(default = "default_client_port")]
    pub client_port: u16,
    #[serde(default = "default_hq_port")]
    pub hq_port: u16,
    #[serde(default = "default_sts_port")]
    pub sts_port: u16,
    #[serde(default = "default_announce_ip")]
    pub announce_game_server_ip: String,
    #[serde(default = "default_announce_port")]
    pub announce_game_server_port: u16,
    #[serde(default = "default_server_id")]
    pub default_server_id: u8,
    #[serde(default = "default_true")]
    pub auto_create_accounts: bool,
    #[serde(default = "default_true")]
    pub development_mode: bool,
    #[serde(default = "default_dev_user")]
    pub default_dev_username: String,
    #[serde(default)]
    pub security: SecurityConfig,
    #[serde(default)]
    pub database: DatabaseConfig,
}

fn default_true() -> bool {
    true
}
fn default_bind() -> String {
    "0.0.0.0".to_string()
}
fn default_client_port() -> u16 {
    2106
}
fn default_hq_port() -> u16 {
    13001
}
fn default_sts_port() -> u16 {
    6600
}
fn default_announce_ip() -> String {
    "192.168.3.184".to_string()
}
fn default_announce_port() -> u16 {
    7777
}
fn default_server_id() -> u8 {
    23
}
fn default_dev_user() -> String {
    String::new()
}
fn default_max_attempts() -> u32 {
    15
}
fn default_ban_minutes() -> u32 {
    15
}
fn default_db_path() -> String {
    "data/Banco de Dados/login.db".to_string()
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            enable_rate_limit: true,
            max_attempts_per_minute: default_max_attempts(),
            temp_ban_minutes: default_ban_minutes(),
        }
    }
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            path: default_db_path(),
        }
    }
}

impl Default for LoginServerConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            bind_address: default_bind(),
            client_port: default_client_port(),
            hq_port: default_hq_port(),
            sts_port: default_sts_port(),
            announce_game_server_ip: default_announce_ip(),
            announce_game_server_port: default_announce_port(),
            default_server_id: default_server_id(),
            auto_create_accounts: true,
            development_mode: true,
            default_dev_username: default_dev_user(),
            security: SecurityConfig::default(),
            database: DatabaseConfig::default(),
        }
    }
}

pub fn load_config(path: &str) -> LoginServerConfig {
    if Path::new(path).exists() {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(val) = json.get("login-server") {
                    if let Ok(cfg) = serde_json::from_value::<LoginServerConfig>(val.clone()) {
                        return cfg;
                    }
                }
            }
        }
    }
    LoginServerConfig::default()
}
