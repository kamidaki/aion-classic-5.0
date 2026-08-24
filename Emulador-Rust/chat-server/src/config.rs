use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct ChatServerConfig {
    #[serde(default = "default_enabled")]
    pub enabled: bool,
    #[serde(default = "default_bind")]
    pub bind_address: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_internal_port")]
    pub internal_port: u16,
    #[serde(default = "default_chat_password")]
    pub chat_password: String,
    #[serde(default = "default_max_channels")]
    pub max_channels: u32,
    #[serde(default = "default_anti_flood")]
    pub anti_flood_messages_per_sec: u32,
}

fn default_enabled() -> bool {
    true
}
fn default_bind() -> String {
    "0.0.0.0".to_string()
}
fn default_port() -> u16 {
    10241
}
fn default_internal_port() -> u16 {
    9021
}
fn default_chat_password() -> String {
    "Sabrewolf100!".to_string()
}
fn default_max_channels() -> u32 {
    500
}
fn default_anti_flood() -> u32 {
    5
}

impl Default for ChatServerConfig {
    fn default() -> Self {
        Self {
            enabled: default_enabled(),
            bind_address: default_bind(),
            port: default_port(),
            internal_port: default_internal_port(),
            chat_password: default_chat_password(),
            max_channels: default_max_channels(),
            anti_flood_messages_per_sec: default_anti_flood(),
        }
    }
}

pub fn load_config(path: &str) -> ChatServerConfig {
    if Path::new(path).exists() {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(chat_val) = json.get("chat-server") {
                    if let Ok(cfg) = serde_json::from_value::<ChatServerConfig>(chat_val.clone()) {
                        return cfg;
                    }
                }
            }
        }
    }
    ChatServerConfig::default()
}
