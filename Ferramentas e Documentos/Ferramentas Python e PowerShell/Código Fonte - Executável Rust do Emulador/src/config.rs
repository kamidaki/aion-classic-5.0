use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io;
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
    #[serde(default = "default_java_dir")]
    pub java_dir: String,
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
    #[serde(default = "default_db_host")]
    pub host: String,
    #[serde(default = "default_db_port")]
    pub port: u16,
    #[serde(default = "default_db_user")]
    pub user: String,
    #[serde(default = "default_db_pass")]
    pub password: String,
    #[serde(default = "default_db_name")]
    pub database: String,
    /// Optional: explicit path to the database.properties file for this DB
    #[serde(default)]
    pub properties_file: String,
    /// Display label for the UI (e.g. "Game Server")
    #[serde(default)]
    pub label: String,
    /// Color tag for the UI card
    #[serde(default)]
    pub color: String,
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
    /// Legacy single-database config (kept for backward compat, prefer `databases`)
    #[serde(default)]
    pub database: DatabaseSettings,
    /// Multi-database map: keys are "gs", "ls", "cs"
    #[serde(default)]
    pub databases: HashMap<String, DatabaseSettings>,
    #[serde(default)]
    pub servers: HashMap<String, ServerConfig>,
}

fn default_true() -> bool { true }
fn default_false() -> bool { false }
fn default_seq_delay() -> u64 { 5 }
fn default_clean_days() -> u32 { 7 }
fn default_base_dir() -> String { ".".to_string() }
fn default_java_dir() -> String { "Config/java-deployment".to_string() }
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
fn default_db_host() -> String { "".to_string() }
fn default_db_name() -> String { "aionclassic_gs".to_string() }
fn default_db_port() -> u16 { 3306 }
fn default_db_user() -> String { "".to_string() }
fn default_db_pass() -> String { "".to_string() }
fn default_java() -> String { "Config/Config/java-deployment/bin/java.exe".to_string() }
fn default_shutdown_delay() -> u64 { 5 }

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
            java_dir: default_java_dir(),
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
            database: "aionclassic_gs".to_string(),
            properties_file: "".to_string(),
            label: "".to_string(),
            color: "".to_string(),
        }
    }
}

fn default_databases() -> HashMap<String, DatabaseSettings> {
    let mut m = HashMap::new();
    m.insert("gs".to_string(), DatabaseSettings {
        auto_read_properties: true,
        host: "".to_string(),
        port: 3306,
        user: "".to_string(),
        password: "".to_string(),
        database: "aionclassic_gs".to_string(),
        properties_file: "GameServer/config/network/database.properties".to_string(),
        label: "Game Server".to_string(),
        color: "#32CD32".to_string(),
    });
    m.insert("ls".to_string(), DatabaseSettings {
        auto_read_properties: true,
        host: "".to_string(),
        port: 3306,
        user: "".to_string(),
        password: "".to_string(),
        database: "aionclassic_ls".to_string(),
        properties_file: "LoginServer/config/network/database.properties".to_string(),
        label: "Login Server".to_string(),
        color: "#FFD700".to_string(),
    });
    m.insert("cs".to_string(), DatabaseSettings {
        auto_read_properties: true,
        host: "".to_string(),
        port: 3306,
        user: "".to_string(),
        password: "".to_string(),
        database: "aionclassic_cs".to_string(),
        properties_file: "ChatServer/config/network/database.properties".to_string(),
        label: "Chat Server".to_string(),
        color: "#00CED1".to_string(),
    });
    m
}

impl Default for RootConfig {
    fn default() -> Self {
        let mut servers = HashMap::new();

        servers.insert(
            "chat".to_string(),
            ServerConfig {
                java_exe: "Config/java-deployment/bin/java.exe".to_string(),
                jvm_args: vec![
                    "-Xms128m".to_string(),
                    "-Xmx256m".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.chatserver.ChatServer".to_string(),
                classpath: "./libs/*;./libs/ChatServer-ClassicEmu-Brasil.jar".to_string(),
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
                java_exe: "Config/java-deployment/bin/java.exe".to_string(),
                jvm_args: vec![
                    "-Xms64m".to_string(),
                    "-Xmx128m".to_string(),
                    "-server".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.loginserver.LoginServer".to_string(),
                classpath: "./libs/*;./libs/LoginServer-ClassicEmu-Brasil.jar".to_string(),
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
                java_exe: "Config/java-deployment/bin/java.exe".to_string(),
                jvm_args: vec![
                    "-Xms1280m".to_string(),
                    "-Xmx3192m".to_string(),
                    "-XX:MaxHeapSize=3192m".to_string(),
                    "-ea".to_string(),
                    "-Dfile.encoding=UTF-8".to_string(),
                    "-DconsoleEncoding=UTF-8".to_string(),
                ],
                main_class: "com.aionemu.gameserver.GameServer".to_string(),
                classpath: "./libs/*;./libs/GameServer-ClassicEmu-Brasil.jar".to_string(),
                working_dir: "GameServer".to_string(),
                label: "Game Server".to_string(),
                tag: "GS".to_string(),
                enabled: true,
                color: "#32CD32".to_string(),
                management_port: None,
                shutdown_delay_seconds: 5,
            },
        );

        Self {
            launcher: LauncherSettings::default(),
            paths: PathsSettings::default(),
            gui: GuiSettings::default(),
            database: DatabaseSettings::default(),
            databases: default_databases(),
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

/// Materializa as credenciais do `config.json` no formato consumido pelos
/// servidores Java. Arquivos completos existentes são preservados, pois podem
/// ter sido configurados manualmente e são a fonte principal quando
/// `auto_read_properties` está habilitado.
pub fn ensure_database_properties(config: &RootConfig) -> io::Result<Vec<String>> {
    let mut database_ids: Vec<&String> = config.databases.keys().collect();
    database_ids.sort();

    let mut generated = Vec::new();
    for database_id in database_ids {
        let database = &config.databases[database_id];
        if database.properties_file.trim().is_empty() {
            continue;
        }

        let path = Path::new(&database.properties_file);
        if let Ok(existing) = fs::read_to_string(path) {
            let mut has_url = false;
            let mut has_user = false;
            let mut has_password = false;
            for line in existing.lines() {
                let trimmed = line.trim_start();
                if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with('!') {
                    continue;
                }
                if let Some((key, _)) = trimmed.split_once('=') {
                    match key.trim() {
                        "database.url" => has_url = true,
                        "database.user" => has_user = true,
                        "database.password" => has_password = true,
                        _ => {}
                    }
                }
            }
            if has_url && has_user && has_password {
                continue;
            }
        }

        if database.host.trim().is_empty()
            || database.user.trim().is_empty()
            || database.database.trim().is_empty()
        {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                format!(
                    "Configuração do banco '{}' incompleta: host, user e database são obrigatórios",
                    database_id
                ),
            ));
        }

        for (field, value) in [
            ("host", &database.host),
            ("user", &database.user),
            ("password", &database.password),
            ("database", &database.database),
        ] {
            if value.contains(['\r', '\n']) {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    format!(
                        "Configuração do banco '{}': o campo {} não pode conter quebra de linha",
                        database_id, field
                    ),
                ));
            }
        }

        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        let content = format!(
            "# Gerado automaticamente pelo Aion Classic - EMULADOR.\n\
database.url=jdbc:mysql://{}:{}/{}?useUnicode=true&characterEncoding=UTF-8&serverTimezone=UTC\n\
database.user={}\n\
database.password={}\n",
            database.host,
            database.port,
            database.database,
            database.user,
            database.password
        );
        fs::write(path, content)?;
        generated.push(path.to_string_lossy().to_string());
    }

    Ok(generated)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn test_directory(name: &str) -> std::path::PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("aion-launcher-{}-{}-{}", name, std::process::id(), unique))
    }

    fn config_for(path: &Path) -> RootConfig {
        let mut config = RootConfig::default();
        config.databases.clear();
        config.databases.insert(
            "gs".to_string(),
            DatabaseSettings {
                auto_read_properties: true,
                host: "127.0.0.1".to_string(),
                port: 3306,
                user: "aion".to_string(),
                password: "secret".to_string(),
                database: "aionclassic_gs".to_string(),
                properties_file: path.to_string_lossy().to_string(),
                label: "Game Server".to_string(),
                color: "#32CD32".to_string(),
            },
        );
        config
    }

    #[test]
    fn creates_missing_database_properties() {
        let dir = test_directory("create");
        let path = dir.join("config/network/database.properties");
        let generated = ensure_database_properties(&config_for(&path)).unwrap();
        let content = fs::read_to_string(&path).unwrap();

        assert_eq!(generated, vec![path.to_string_lossy().to_string()]);
        assert!(content.contains("database.url=jdbc:mysql://127.0.0.1:3306/aionclassic_gs"));
        assert!(content.contains("database.user=aion"));
        assert!(content.contains("database.password=secret"));

        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn preserves_complete_existing_database_properties() {
        let dir = test_directory("preserve");
        let path = dir.join("database.properties");
        fs::create_dir_all(&dir).unwrap();
        let original = "database.url=jdbc:mysql://db.internal:3307/custom\ndatabase.user=manual\ndatabase.password=manual-secret\n";
        fs::write(&path, original).unwrap();

        let generated = ensure_database_properties(&config_for(&path)).unwrap();

        assert!(generated.is_empty());
        assert_eq!(fs::read_to_string(&path).unwrap(), original);
        fs::remove_dir_all(dir).unwrap();
    }
}
