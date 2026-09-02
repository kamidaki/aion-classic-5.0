use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct LauncherSettings {
    #[serde(default = "default_false")]
    pub start_with_windows: bool,
    #[serde(default = "default_true")]
    pub auto_start_servers_on_launch: bool,
    #[serde(default = "default_seq_delay")]
    pub start_sequence_delay_seconds: u64,
    #[serde(default = "default_clean_days")]
    pub clean_archived_logs_days: u32,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct PathsSettings {
    #[serde(default = "default_base_dir")]
    pub base_dir: String,
    #[serde(default = "default_chat_dir")]
    pub chat_server_dir: String,
    #[serde(default = "default_login_dir")]
    pub login_server_dir: String,
    #[serde(default = "default_game_dir")]
    pub game_server_dir: String,
    #[serde(default = "default_chat_log")]
    pub chat_server_log_dir: String,
    #[serde(default = "default_login_log")]
    pub login_server_log_dir: String,
    #[serde(default = "default_game_log")]
    pub game_server_log_dir: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct GuiSettings {
    #[serde(default = "default_theme")]
    pub theme: String,
    #[serde(default = "default_width")]
    pub window_width: u32,
    #[serde(default = "default_height")]
    pub window_height: u32,
    #[serde(default = "default_http_port")]
    pub http_port: u16,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DatabaseSettings {
    #[serde(default = "default_true")]
    pub auto_read_properties: bool,
    #[serde(default = "default_empty")]
    pub host: String,
    #[serde(default = "default_db_port")]
    pub port: u16,
    #[serde(default = "default_empty")]
    pub user: String,
    #[serde(default = "default_empty")]
    pub password: String,
    #[serde(default = "default_db_name")]
    pub database: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ServerConfig {
    #[serde(default = "default_java")]
    pub java_exe: String,
    #[serde(default)]
    pub jvm_args: Vec<String>,
    pub main_class: String,
    pub classpath: String,
    #[serde(default = "default_empty")]
    pub working_dir: String,
    pub label: String,
    pub tag: String,
    #[serde(default = "default_true")]
    pub enabled: bool,
    pub color: String,
    #[serde(default)]
    pub management_port: Option<u16>,
    #[serde(default = "default_shutdown_delay")]
    pub shutdown_delay_seconds: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct RootConfig {
    #[serde(default)]
    pub launcher: LauncherSettings,
    #[serde(default)]
    pub paths: PathsSettings,
    #[serde(default)]
    pub gui: GuiSettings,
    #[serde(default)]
    pub database: DatabaseSettings,
    #[serde(default)]
    pub servers: HashMap<String, ServerConfig>,
}

fn default_true() -> bool { true }
fn default_false() -> bool { false }
fn default_seq_delay() -> u64 { 5 }
fn default_clean_days() -> u32 { 7 }
fn default_base_dir() -> String { ".".to_string() }
fn default_chat_dir() -> String { "ChatServer".to_string() }
fn default_login_dir() -> String { "LoginServer".to_string() }
fn default_game_dir() -> String { "GameServer".to_string() }
fn default_chat_log() -> String { "ChatServer/log".to_string() }
fn default_login_log() -> String { "LoginServer/log".to_string() }
fn default_game_log() -> String { "GameServer/log".to_string() }
fn default_theme() -> String { "dark".to_string() }
fn default_width() -> u32 { 1440 }
fn default_height() -> u32 { 900 }
fn default_http_port() -> u16 { 18080 }
fn default_empty() -> String { "".to_string() }
fn default_db_name() -> String { "aiondbls_gs".to_string() }
fn default_db_port() -> u16 { 3306 }
fn default_java() -> String { "java".to_string() }
fn default_shutdown_delay() -> u64 { 60 }

impl Default for LauncherSettings {
    fn default() -> Self {
        Self {
            start_with_windows: false,
            auto_start_servers_on_launch: true,
            start_sequence_delay_seconds: default_seq_delay(),
            clean_archived_logs_days: default_clean_days(),
        }
    }
}

impl Default for PathsSettings {
    fn default() -> Self {
        Self {
            base_dir: default_base_dir(),
            chat_server_dir: default_chat_dir(),
            login_server_dir: default_login_dir(),
            game_server_dir: default_game_dir(),
            chat_server_log_dir: default_chat_log(),
            login_server_log_dir: default_login_log(),
            game_server_log_dir: default_game_log(),
        }
    }
}

impl Default for GuiSettings {
    fn default() -> Self {
        Self {
            theme: default_theme(),
            window_width: default_width(),
            window_height: default_height(),
            http_port: default_http_port(),
        }
    }
}

impl Default for DatabaseSettings {
    fn default() -> Self {
        Self {
            auto_read_properties: true,
            host: "".to_string(),
            port: 3306,
            user: "".to_string(),
            password: "".to_string(),
            database: "aiondbls_gs".to_string(),
        }
    }
}

impl Default for RootConfig {
    fn default() -> Self {
        let mut servers = HashMap::new();

        servers.insert(
            "chat".to_string(),
            ServerConfig {
                java_exe: "java".to_string(),
                jvm_args: vec![
                    "-Xms128m".to_string(),
                    "-Xmx256m".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.chatserver.ChatServer".to_string(),
                classpath: "./libs/*;ChatServer-ClassicEmu-Brasil.jar;./libs/ChatServer-ClassicEmu-Brasil.jar".to_string(),
                working_dir: "ChatServer".to_string(),
                label: "Chat Server".to_string(),
                tag: "CS".to_string(),
                enabled: true,
                color: "#00CED1".to_string(),
                management_port: None,
                shutdown_delay_seconds: 5,
            },
        );

        servers.insert(
            "login".to_string(),
            ServerConfig {
                java_exe: "java".to_string(),
                jvm_args: vec![
                    "-Xms64m".to_string(),
                    "-Xmx128m".to_string(),
                    "-server".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.loginserver.LoginServer".to_string(),
                classpath: "./libs/*;LoginServer-ClassicEmu-Brasil.jar;./libs/LoginServer-ClassicEmu-Brasil.jar".to_string(),
                working_dir: "LoginServer".to_string(),
                label: "Login Server".to_string(),
                tag: "LS".to_string(),
                enabled: true,
                color: "#FFD700".to_string(),
                management_port: None,
                shutdown_delay_seconds: 5,
            },
        );

        servers.insert(
            "game".to_string(),
            ServerConfig {
                java_exe: "java".to_string(),
                jvm_args: vec![
                    "-Xms1280m".to_string(),
                    "-Xmx3192m".to_string(),
                    "-XX:MaxHeapSize=3192m".to_string(),
                    "-ea".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.gameserver.GameServer".to_string(),
                classpath: "./libs/*;GameServer-ClassicEmu-Brasil.jar;./libs/GameServer-ClassicEmu-Brasil.jar".to_string(),
                working_dir: "GameServer".to_string(),
                label: "Game Server".to_string(),
                tag: "GS".to_string(),
                enabled: true,
                color: "#32CD32".to_string(),
                management_port: Some(18091),
                shutdown_delay_seconds: 60,
            },
        );

        Self {
            launcher: LauncherSettings::default(),
            paths: PathsSettings::default(),
            gui: GuiSettings::default(),
            database: DatabaseSettings::default(),
            servers,
        }
    }
}

pub fn load_config(path_str: &str) -> RootConfig {
    let p = Path::new(path_str);
    if p.exists() {
        if let Ok(content) = fs::read_to_string(p) {
            if let Ok(cfg) = serde_json::from_str::<RootConfig>(&content) {
                return cfg;
            }
        }
    }

    let default_cfg = RootConfig::default();
    if let Ok(json) = serde_json::to_string_pretty(&default_cfg) {
        let _ = fs::write(p, json);
    }
    default_cfg
}
