//! Configuration module for Aion Classic Login Server.
//!
//! Submodules:
//! - [`security_config`] — Rate-limiting & brute force protection settings
//! - [`database_config`] — SQLite database connection settings
//! - [`network_config`] — Ports & binding IPs for NCSoft, HQ, STS and Inter-Server

pub mod security_config;
pub mod database_config;
pub mod network_config;

pub use security_config::SecurityConfig;
pub use database_config::DatabaseConfig;
pub use network_config::NetworkConfig;

use serde::Deserialize;
use std::fs;
use std::path::Path;

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
    #[serde(default = "default_gameserver_port")]
    pub gameserver_port: u16,
    #[serde(default = "default_gameserver_password")]
    pub gameserver_password: String,
    #[serde(default = "default_announce_ip")]
    pub announce_game_server_ip: String,
    #[serde(default = "default_announce_port")]
    pub announce_game_server_port: u16,
    #[serde(default = "default_server_id")]
    pub default_server_id: u8,
    #[serde(default = "default_true")]
    pub auto_create_accounts: bool,
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
fn default_gameserver_port() -> u16 {
    9014
}
fn default_gameserver_password() -> String {
    "Sabrewolf100!".to_string()
}
fn default_announce_ip() -> String {
    "127.0.0.1".to_string()
}
fn default_announce_port() -> u16 {
    7777
}
fn default_server_id() -> u8 {
    1
}
fn default_dev_user() -> String {
    String::new()
}

impl Default for LoginServerConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            bind_address: default_bind(),
            client_port: default_client_port(),
            hq_port: default_hq_port(),
            sts_port: default_sts_port(),
            gameserver_port: default_gameserver_port(),
            gameserver_password: default_gameserver_password(),
            announce_game_server_ip: default_announce_ip(),
            announce_game_server_port: default_announce_port(),
            default_server_id: default_server_id(),
            auto_create_accounts: true,
            default_dev_username: default_dev_user(),
            security: SecurityConfig::default(),
            database: DatabaseConfig::default(),
        }
    }
}

pub fn load_config(path: &str) -> LoginServerConfig {
    let mut config = LoginServerConfig::default();

    // 1. Prioriza loginserver.properties
    let properties_candidates = [
        "config/loginserver.properties",
        "../Produto Final/config/loginserver.properties",
        "../../Produto Final/config/loginserver.properties",
        "loginserver.properties",
    ];

    for prop_path in properties_candidates {
        if Path::new(prop_path).exists() {
            if let Ok(props) = commons::Properties::load_from_file(prop_path) {
                println!("INFO: Loaded Login config from {prop_path} (.properties)");
                config.bind_address = props.get_string("loginserver.network.bind.address", &config.bind_address);
                config.client_port = props.get_u16("loginserver.network.client.port", config.client_port);
                config.hq_port = props.get_u16("loginserver.network.hq.port", config.hq_port);
                config.sts_port = props.get_u16("loginserver.network.sts.port", config.sts_port);
                config.gameserver_port = props.get_u16("loginserver.network.gameserver.port", config.gameserver_port);
                config.gameserver_password = props.get_string("loginserver.network.gameserver.password", &config.gameserver_password);
                config.announce_game_server_ip = props.get_string("loginserver.network.announce.gameserver.ip", &config.announce_game_server_ip);
                config.announce_game_server_port = props.get_u16("loginserver.network.announce.gameserver.port", config.announce_game_server_port);
                config.default_server_id = props.get_u8("loginserver.network.default.server.id", config.default_server_id);
                config.auto_create_accounts = props.get_bool("loginserver.auto.create.accounts", config.auto_create_accounts);
                config.database.path = props.get_string("loginserver.database.path", &config.database.path);
                config.security.enable_rate_limit = props.get_bool("loginserver.security.rate.limit.enable", config.security.enable_rate_limit);
                config.security.max_attempts_per_minute = props.get_u32("loginserver.security.max.attempts.per.minute", config.security.max_attempts_per_minute);
                config.security.temp_ban_minutes = props.get_u32("loginserver.security.temp.ban.minutes", config.security.temp_ban_minutes);
                return config;
            }
        }
    }

    // 2. Fallback para launcher.json se fornecido
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

    config
}
