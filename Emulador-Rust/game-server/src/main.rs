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

mod data_loader;
mod db;
mod error;
mod game;

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
}

#[derive(Debug, Deserialize, Clone)]
pub struct NetworkConfig {
    #[serde(default = "default_bind_address")]
    pub bind_address: String,
    #[serde(default = "default_port")]
    pub port: u16,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            bind_address: default_bind_address(),
            port: default_port(),
        }
    }
}

fn default_bind_address() -> String {
    "0.0.0.0".to_string()
}
fn default_port() -> u16 {
    7777
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerInfoConfig {
    #[serde(default = "default_server_id")]
    pub server_id: u8,
    #[serde(default = "default_server_name")]
    pub server_name: String,
    #[serde(default = "default_tick_rate")]
    pub tick_rate: f32,
}

impl Default for ServerInfoConfig {
    fn default() -> Self {
        Self {
            server_id: default_server_id(),
            server_name: default_server_name(),
            tick_rate: default_tick_rate(),
        }
    }
}

fn default_server_id() -> u8 {
    23
}
fn default_server_name() -> String {
    "Atreia".to_string()
}
fn default_tick_rate() -> f32 {
    144.0
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
    "aion.db".to_string()
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
    let candidates = [
        "config/game_server.toml",
        "../config/game_server.toml",
        "game_server.toml",
    ];

    for path in candidates {
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

