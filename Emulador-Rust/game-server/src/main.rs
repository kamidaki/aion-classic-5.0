//! This server is responsible for the game protocol, this protocol starts once
//! the client has picked a server, the IP Address of the choson server is this
//! game server instance.
//!
//! # The protocol
//! - The first two bytes of every message are the length, a packet *CAN* contain
//! more than one message
//! - The length which includes its own bytes is follow by an encrypted payload.
//! This payload is some kind of XOR shift with a hardcoded starting key of
//! `nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9`
//!
//! 1. The client begins the protocol by connecting to a game server instance and
//! waiting for a message
//! 2. The server sends a packet where bytes 0-4 of the payload are static
//! `[0xc8,0x01,0x40,0x37,0xfe]` then 4 bytes which are a random key
//! 3. The server then responds with a payload about the client version, looks
//! like OS version info from `GetVersionExA` and `GetACP` for the ANSI format

mod chat_connector;
pub mod dao;
mod data_loader;
pub mod db;
mod error;
mod game;
mod login_connector;
pub mod network;
pub use game::controller;

use crossbeam_channel::Sender;
use data_loader::GameData;
use db::Db;
use game::{ClientUpdate, Connection, ServerUpdate};
use std::collections::HashMap;
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::thread::spawn;
use std::time::Duration;

use error::Error;
use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct GameServerConfig {
    #[serde(default)]
    pub network: NetworkConfig,
    #[serde(default)]
    pub server: ServerInfoConfig,
    #[serde(default)]
    pub database: DatabaseConfig,
    #[serde(default)]
    pub world: WorldConfig,
    #[serde(default)]
    pub security: SecurityConfig,
    #[serde(default)]
    pub inter_server: InterServerConfig,
    #[serde(default)]
    pub gameplay: GameplayConfig,
}

impl Default for GameServerConfig {
    fn default() -> Self {
        Self {
            network: NetworkConfig::default(),
            server: ServerInfoConfig::default(),
            database: DatabaseConfig::default(),
            world: WorldConfig::default(),
            security: SecurityConfig::default(),
            inter_server: InterServerConfig::default(),
            gameplay: GameplayConfig::default(),
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct InterServerConfig {
    #[serde(default = "default_login_address")]
    pub login_server_address: String,
    #[serde(default = "default_gameserver_password")]
    pub gameserver_password: String,
    #[serde(default = "default_chat_address")]
    pub chat_server_address: String,
    #[serde(default = "default_chat_password")]
    pub chat_password: String,
}

impl Default for InterServerConfig {
    fn default() -> Self {
        Self {
            login_server_address: default_login_address(),
            gameserver_password: default_gameserver_password(),
            chat_server_address: default_chat_address(),
            chat_password: default_chat_password(),
        }
    }
}

fn default_login_address() -> String {
    "127.0.0.1:9014".to_string()
}
fn default_gameserver_password() -> String {
    "Sabrewolf100!".to_string()
}
fn default_chat_address() -> String {
    "127.0.0.1:9021".to_string()
}
fn default_chat_password() -> String {
    "Sabrewolf100!".to_string()
}

#[derive(Debug, Deserialize, Clone)]
pub struct NetworkConfig {
    #[serde(default = "default_bind_address")]
    pub bind_address: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_max_players")]
    pub max_players: u32,
    #[serde(default = "default_nio_threads")]
    pub nio_threads: u32,
    #[serde(default = "default_processor_threads_min")]
    pub processor_threads_min: u32,
    #[serde(default = "default_processor_threads_max")]
    pub processor_threads_max: u32,
    #[serde(default = "default_threshold_kill")]
    pub processor_threshold_kill: u32,
    #[serde(default = "default_threshold_spawn")]
    pub processor_threshold_spawn: u32,
    #[serde(default = "default_false")]
    pub display_unknown_packets: bool,
    #[serde(default = "default_false")]
    pub display_packets: bool,
    #[serde(default)]
    pub flood_protection: FloodProtectionConfig,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            bind_address: default_bind_address(),
            port: default_port(),
            max_players: default_max_players(),
            nio_threads: default_nio_threads(),
            processor_threads_min: default_processor_threads_min(),
            processor_threads_max: default_processor_threads_max(),
            processor_threshold_kill: default_threshold_kill(),
            processor_threshold_spawn: default_threshold_spawn(),
            display_unknown_packets: false,
            display_packets: false,
            flood_protection: FloodProtectionConfig::default(),
        }
    }
}

fn default_bind_address() -> String {
    "0.0.0.0".to_string()
}
fn default_port() -> u16 {
    7777
}
fn default_nio_threads() -> u32 {
    4
}
fn default_processor_threads_min() -> u32 {
    4
}
fn default_processor_threads_max() -> u32 {
    16
}
fn default_threshold_kill() -> u32 {
    3
}
fn default_threshold_spawn() -> u32 {
    50
}
fn default_false() -> bool {
    false
}
fn default_1000() -> u32 {
    1000
}
fn default_10() -> u32 {
    10
}
fn default_20() -> u32 {
    20
}
fn default_30() -> u32 {
    30
}
fn default_60() -> u32 {
    60
}

#[derive(Debug, Deserialize, Clone)]
pub struct FloodProtectionConfig {
    #[serde(default = "default_false")]
    pub enabled: bool,
    #[serde(default = "default_1000")]
    pub tick_ms: u32,
    #[serde(default = "default_10")]
    pub short_warn: u32,
    #[serde(default = "default_20")]
    pub short_reject: u32,
    #[serde(default = "default_30")]
    pub long_warn: u32,
    #[serde(default = "default_60")]
    pub long_reject: u32,
}

impl Default for FloodProtectionConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            tick_ms: 1000,
            short_warn: 10,
            short_reject: 20,
            long_warn: 30,
            long_reject: 60,
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct GameplayConfig {
    #[serde(default = "default_country_code")]
    pub country_code: u8,
    #[serde(default = "default_true")]
    pub chat_server_enable: bool,
    #[serde(default = "default_false")]
    pub display_revision: bool,
    #[serde(default = "default_char_limit")]
    pub character_limit_count: u8,
    #[serde(default = "default_char_creation_mode")]
    pub character_creation_mode: u8,
    #[serde(default = "default_max_level")]
    pub players_max_level: u8,
    #[serde(default = "default_1")]
    pub starting_level: u8,
    #[serde(default = "default_10_u8")]
    pub start_class_max_level: u8,
    #[serde(default = "default_name_pattern")]
    pub character_name_pattern: String,
    #[serde(default = "default_20")]
    pub character_reentry_time_secs: u32,
}

fn default_country_code() -> u8 {
    2
}
fn default_char_limit() -> u8 {
    8
}
fn default_char_creation_mode() -> u8 {
    1
}
fn default_max_level() -> u8 {
    55
}
fn default_1() -> u8 {
    1
}
fn default_10_u8() -> u8 {
    10
}
fn default_name_pattern() -> String {
    "^[a-zA-Z0-9]{2,16}$".to_string()
}

impl Default for GameplayConfig {
    fn default() -> Self {
        Self {
            country_code: default_country_code(),
            chat_server_enable: true,
            display_revision: false,
            character_limit_count: default_char_limit(),
            character_creation_mode: default_char_creation_mode(),
            players_max_level: default_max_level(),
            starting_level: default_1(),
            start_class_max_level: default_10_u8(),
            character_name_pattern: default_name_pattern(),
            character_reentry_time_secs: default_20(),
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerInfoConfig {
    #[serde(default = "default_server_id")]
    pub server_id: u8,
    #[serde(default = "default_server_name")]
    pub server_name: String,
    #[serde(default = "default_tick_rate")]
    pub tick_rate: f32,
    #[serde(default = "default_max_players")]
    pub max_players: u32,
}

impl Default for ServerInfoConfig {
    fn default() -> Self {
        Self {
            server_id: default_server_id(),
            server_name: default_server_name(),
            tick_rate: default_tick_rate(),
            max_players: default_max_players(),
        }
    }
}

fn default_server_id() -> u8 {
    1
}
fn default_server_name() -> String {
    "Brasil em Chamas (São Paulo)".to_string()
}
fn default_tick_rate() -> f32 {
    20.0
}
fn default_max_players() -> u32 {
    1000
}

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    #[serde(default = "default_db_path")]
    pub database_path: String,
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            database_path: default_db_path(),
        }
    }
}

fn default_db_path() -> String {
    "data/Banco de Dados/game.db".to_string()
}

#[derive(Debug, Deserialize, Clone)]
pub struct WorldConfig {
    #[serde(default = "default_data_dir")]
    pub data_dir: String,
    #[serde(default = "default_spawns_file")]
    pub spawns_file: String,
    #[serde(default = "default_kit_file")]
    pub initial_kit_file: String,
    #[serde(default = "default_vision_radius")]
    pub vision_radius: f32,
}

impl Default for WorldConfig {
    fn default() -> Self {
        Self {
            data_dir: default_data_dir(),
            spawns_file: default_spawns_file(),
            initial_kit_file: default_kit_file(),
            vision_radius: default_vision_radius(),
        }
    }
}

fn default_data_dir() -> String {
    "data/client".to_string()
}
fn default_spawns_file() -> String {
    "data/spawns.csv".to_string()
}
fn default_kit_file() -> String {
    "data/itens_iniciais.csv".to_string()
}
fn default_vision_radius() -> f32 {
    100.0
}

#[derive(Debug, Deserialize, Clone)]
pub struct SecurityConfig {
    #[serde(default = "default_true")]
    pub require_valid_session: bool,
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            require_valid_session: true,
        }
    }
}

fn default_true() -> bool {
    true
}

fn load_config() -> GameServerConfig {
    // 1. Prioriza config/launcher.json
    let launcher_candidates = [
        "config/launcher.json",
        "../Produto Final/config/launcher.json",
        "launcher.json",
    ];

    for path in launcher_candidates {
        if let Ok(content) = std::fs::read_to_string(path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(gs_val) = json.get("game-server") {
                    println!("INFO: Loaded Game config from {path} (JSON)");
                    let mut cfg = GameServerConfig::default();

                    if let Some(b) = gs_val.get("bind_address").and_then(|v| v.as_str()) {
                        cfg.network.bind_address = b.to_string();
                    }
                    if let Some(p) = gs_val.get("port").and_then(|v| v.as_u64()) {
                        cfg.network.port = p as u16;
                    }
                    if let Some(id) = gs_val.get("server_id").and_then(|v| v.as_u64()) {
                        cfg.server.server_id = id as u8;
                    }
                    if let Some(name) = gs_val.get("server_name").and_then(|v| v.as_str()) {
                        cfg.server.server_name = name.to_string();
                    }
                    if let Some(max_p) = gs_val.get("max_players").and_then(|v| v.as_u64()) {
                        cfg.server.max_players = max_p as u32;
                        cfg.network.max_players = max_p as u32;
                    }
                    if let Some(nio) = gs_val.get("nio_threads").and_then(|v| v.as_u64()) {
                        cfg.network.nio_threads = nio as u32;
                    }
                    if let Some(p_min) = gs_val.get("processor_threads_min").and_then(|v| v.as_u64()) {
                        cfg.network.processor_threads_min = p_min as u32;
                    }
                    if let Some(p_max) = gs_val.get("processor_threads_max").and_then(|v| v.as_u64()) {
                        cfg.network.processor_threads_max = p_max as u32;
                    }
                    if let Some(t_kill) = gs_val.get("processor_threshold_kill").and_then(|v| v.as_u64()) {
                        cfg.network.processor_threshold_kill = t_kill as u32;
                    }
                    if let Some(t_spawn) = gs_val.get("processor_threshold_spawn").and_then(|v| v.as_u64()) {
                        cfg.network.processor_threshold_spawn = t_spawn as u32;
                    }
                    if let Some(u_pkt) = gs_val.get("display_unknown_packets").and_then(|v| v.as_bool()) {
                        cfg.network.display_unknown_packets = u_pkt;
                    }
                    if let Some(d_pkt) = gs_val.get("display_packets").and_then(|v| v.as_bool()) {
                        cfg.network.display_packets = d_pkt;
                    }

                    if let Some(la) = gs_val.get("login_server_address").and_then(|v| v.as_str()) {
                        cfg.inter_server.login_server_address = la.to_string();
                    }
                    if let Some(lp) = gs_val.get("gameserver_password").and_then(|v| v.as_str()) {
                        cfg.inter_server.gameserver_password = lp.to_string();
                    }
                    if let Some(ca) = gs_val.get("chat_server_address").and_then(|v| v.as_str()) {
                        cfg.inter_server.chat_server_address = ca.to_string();
                    }
                    if let Some(cp) = gs_val.get("chat_password").and_then(|v| v.as_str()) {
                        cfg.inter_server.chat_password = cp.to_string();
                    }
                    if let Some(db_path) = gs_val.get("database").and_then(|d| d.get("path")).and_then(|v| v.as_str()) {
                        cfg.database.database_path = db_path.to_string();
                    }
                    if let Some(d_path) = gs_val.get("data_path").and_then(|v| v.as_str()) {
                        cfg.world.data_dir = d_path.to_string();
                    }

                    // Gameplay configs
                    if let Some(gp) = gs_val.get("gameplay") {
                        if let Some(cc) = gp.get("country_code").and_then(|v| v.as_u64()) {
                            cfg.gameplay.country_code = cc as u8;
                        }
                        if let Some(cs_en) = gp.get("chat_server_enable").and_then(|v| v.as_bool()) {
                            cfg.gameplay.chat_server_enable = cs_en;
                        }
                        if let Some(rev) = gp.get("display_revision").and_then(|v| v.as_bool()) {
                            cfg.gameplay.display_revision = rev;
                        }
                        if let Some(cl) = gp.get("character_limit_count").and_then(|v| v.as_u64()) {
                            cfg.gameplay.character_limit_count = cl as u8;
                        }
                        if let Some(cm) = gp.get("character_creation_mode").and_then(|v| v.as_u64()) {
                            cfg.gameplay.character_creation_mode = cm as u8;
                        }
                        if let Some(lvl) = gp.get("players_max_level").and_then(|v| v.as_u64()) {
                            cfg.gameplay.players_max_level = lvl as u8;
                        }
                        if let Some(pat) = gp.get("character_name_pattern").and_then(|v| v.as_str()) {
                            cfg.gameplay.character_name_pattern = pat.to_string();
                        }
                        if let Some(rt) = gp.get("character_reentry_time_secs").and_then(|v| v.as_u64()) {
                            cfg.gameplay.character_reentry_time_secs = rt as u32;
                        }
                    }

                    return cfg;
                }
            }
        }
    }

    let toml_candidates = [
        "config/game_server.toml",
        "../config/game_server.toml",
        "game_server.toml",
    ];

    for path in toml_candidates {
        if let Ok(content) = std::fs::read_to_string(path) {
            if let Ok(cfg) = toml::from_str::<GameServerConfig>(&content) {
                println!("INFO: Loaded Game config from {path}");
                return cfg;
            }
        }
    }

    println!("INFO: Using default Game config");
    GameServerConfig {
        network: NetworkConfig::default(),
        server: ServerInfoConfig::default(),
        database: DatabaseConfig::default(),
        world: WorldConfig::default(),
        security: SecurityConfig::default(),
        inter_server: InterServerConfig::default(),
        gameplay: GameplayConfig::default(),
    }
}

fn find_data_dir(configured: &str) -> PathBuf {
    if let Ok(dir) = std::env::var("AION_DATA_DIR") {
        let p = PathBuf::from(dir);
        if p.exists() {
            return p;
        }
    }

    let configured_path = PathBuf::from(configured);
    if configured_path.exists() {
        return configured_path;
    }

    let candidates = [
        "data/client",
        "data",
        "../data/client",
        "../data",
        "../extracted_xml",
        "extracted_xml",
    ];

    for c in candidates {
        let p = PathBuf::from(c);
        if p.exists() {
            return p;
        }
    }

    PathBuf::from("data/client")
}

fn main() {
    let _instance_guard = match commons::single_instance::SingleInstanceGuard::acquire(
        "Game Server",
        "Local\\EmuRust_GameServer_Mutex",
    ) {
        Some(g) => g,
        None => {
            std::process::exit(1);
        }
    };

    println!("INFO: Starting Game Server");
    let config = load_config();

    // Configura flags de log de pacotes
    game::message::set_packet_logging_flags(
        config.network.display_packets,
        config.network.display_unknown_packets,
    );

    println!(
        "INFO: Network Config -> Threads: NIO={}, Processor Min/Max={}/{}, Threshold Spawn/Kill={}/{}, Display Unknown Packets: {}",
        config.network.nio_threads,
        config.network.processor_threads_min,
        config.network.processor_threads_max,
        config.network.processor_threshold_spawn,
        config.network.processor_threshold_kill,
        config.network.display_unknown_packets,
    );
    println!(
        "INFO: Gameplay Config -> CountryCode={}, MaxPlayers={}, CharLimit={}, CreationMode={}, MaxLevel={}, ReentryTime={}s",
        config.gameplay.country_code,
        config.server.max_players,
        config.gameplay.character_limit_count,
        config.gameplay.character_creation_mode,
        config.gameplay.players_max_level,
        config.gameplay.character_reentry_time_secs,
    );

    // Inicia conectores inter-servidores (Java Architecture)
    login_connector::start_login_connector(login_connector::LoginConnectorConfig {
        login_address: config.inter_server.login_server_address.clone(),
        server_id: config.server.server_id,
        game_port: config.network.port,
        max_players: config.server.max_players,
        password: config.inter_server.gameserver_password.clone(),
    });

    chat_connector::start_chat_connector(chat_connector::ChatConnectorConfig {
        chat_address: config.inter_server.chat_server_address.clone(),
        server_id: config.server.server_id,
        password: config.inter_server.chat_password.clone(),
    });

    let db = Db::open(&config.database.database_path).expect("failed to open SQLite db");
    db.migrate().expect("failed to migrate SQLite schema");
    println!("INFO: Opened and migrated DB at {}", config.database.database_path);

    let data_dir = find_data_dir(&config.world.data_dir);
    println!("INFO: Loading game data from {}", data_dir.display());
    let game_data = Arc::new({
        let mut gd = GameData::load(&data_dir);
        let spawns = std::env::var("AION_SPAWNS")
            .unwrap_or_else(|_| config.world.spawns_file.clone());
        gd.carrega_spawns(std::path::Path::new(&spawns));
        let kit = std::env::var("AION_ITENS_INICIAIS")
            .unwrap_or_else(|_| config.world.initial_kit_file.clone());
        gd.carrega_itens_iniciais(std::path::Path::new(&kit));
        gd
    });

    let bind_addr = format!("{}:{}", config.network.bind_address, config.network.port);
    let listener = TcpListener::bind(&bind_addr).unwrap();
    println!("INFO: Listening on {}", listener.local_addr().unwrap());
    println!("INFO: Listening on {}", listener.local_addr().unwrap());

    let clients = Arc::new(Mutex::new(HashMap::new()));
    let (server_tx, server_rx) = crossbeam_channel::bounded(1000);

    let connections = clients.clone();
    let gd = game_data.clone();
    spawn(move || game::game_update(connections, server_rx, db, gd));

    while let Ok((stream, peer)) = listener.accept() {
        println!("INFO: TCP accept from {peer}");
        let connections = clients.clone();
        let server_tx = server_tx.clone();
        spawn(move || {
            if let Err(e) = handle(stream, connections, server_tx) {
                println!("ERROR: session {peer} ended: {e:?}");
            }
        });
    }
}

fn handle(
    stream: TcpStream,
    clients: Arc<Mutex<HashMap<u16, Sender<Vec<ServerUpdate>>>>>,
    server_tx: Sender<ClientUpdate>,
) -> error::Result<()> {
    let peer_addr = stream.peer_addr().map_err(Error::PeerAddr)?;
    let client_id = peer_addr.port();
    println!("INFO: new session {peer_addr}");

    stream
        .set_read_timeout(Some(Duration::from_millis(20)))
        .map_err(Error::SetStreamTimeout)?;
    //    stream
    //        .set_write_timeout(Some(Duration::from_secs(60)))
    //        .map_err(Error::SetStreamTimeout)?;

    let (client_tx, client_rx) = crossbeam_channel::bounded::<Vec<ServerUpdate>>(100);
    clients.lock().unwrap().insert(client_id, client_tx);
    Connection::new(stream, client_id, client_rx, server_tx).handle();

    clients.lock().unwrap().remove(&peer_addr.port());
    println!("INFO: Connection closed from {peer_addr}");

    Ok(())
}

