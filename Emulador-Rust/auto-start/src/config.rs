use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct GuiConfig {
    #[serde(default = "default_theme")]
    pub theme: String,
    #[serde(default = "default_width")]
    pub window_width: u32,
    #[serde(default = "default_height")]
    pub window_height: u32,
    #[serde(default = "default_http_port")]
    pub http_port: u16,
}

#[allow(non_snake_case)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct LauncherConfig {
    #[serde(default = "default_true")]
    pub autoStartLoginServer: bool,
    #[serde(default = "default_true")]
    pub autoStartGameServer: bool,
    #[serde(default = "default_true")]
    pub autoStartChatServer: bool,
    #[serde(default = "default_true")]
    pub restartOnCrash: bool,
    #[serde(default = "default_delay")]
    pub crashRestartDelayMs: u64,
    #[serde(default)]
    pub gui: GuiConfig,
}

#[allow(non_snake_case)]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct LoggingConfig {
    #[serde(default = "default_retention")]
    pub retentionDays: u32,
    #[serde(default = "default_login_log")]
    pub loginServerPath: String,
    #[serde(default = "default_game_log")]
    pub gameServerPath: String,
    #[serde(default = "default_chat_log")]
    pub chatServerPath: String,
}

fn default_true() -> bool { true }
fn default_theme() -> String { "dark".to_string() }
fn default_width() -> u32 { 1150 }
fn default_height() -> u32 { 760 }
fn default_http_port() -> u16 { 18080 }
fn default_delay() -> u64 { 2000 }
fn default_retention() -> u32 { 10 }
fn default_login_log() -> String { "logs/login-server".to_string() }
fn default_game_log() -> String { "logs/game-server".to_string() }
fn default_chat_log() -> String { "logs/chat-server".to_string() }

impl Default for GuiConfig {
    fn default() -> Self {
        Self {
            theme: default_theme(),
            window_width: default_width(),
            window_height: default_height(),
            http_port: default_http_port(),
        }
    }
}

impl Default for LauncherConfig {
    fn default() -> Self {
        Self {
            autoStartLoginServer: true,
            autoStartGameServer: true,
            autoStartChatServer: true,
            restartOnCrash: true,
            crashRestartDelayMs: default_delay(),
            gui: GuiConfig::default(),
        }
    }
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            retentionDays: default_retention(),
            loginServerPath: default_login_log(),
            gameServerPath: default_game_log(),
            chatServerPath: default_chat_log(),
        }
    }
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct RootConfig {
    #[serde(default)]
    pub launcher: LauncherConfig,
    #[serde(default)]
    pub logging: LoggingConfig,
}

pub fn load_config(path: &str) -> RootConfig {
    if Path::new(path).exists() {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(cfg) = serde_json::from_str::<RootConfig>(&content) {
                return cfg;
            }
        }
    }
    RootConfig {
        launcher: LauncherConfig::default(),
        logging: LoggingConfig::default(),
    }
}
