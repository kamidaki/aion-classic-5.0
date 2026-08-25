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
