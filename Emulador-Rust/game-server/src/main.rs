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

pub mod admin;
pub mod ai;
pub mod arena;
pub mod broker;
pub mod character;
mod chat_connector;
pub mod controller;
pub mod craft;
pub mod cron_events;
pub mod dao;
pub mod data;
pub mod dataholders;
pub mod data_loader;
pub mod db;
pub mod enchant;
pub mod engine;
pub mod engine_loop;
pub mod entity;
pub mod environment;
mod error;
pub mod geoengine;
pub mod guild;
pub mod housing;
pub mod instance;
mod login_connector;
pub mod mail;
pub mod message;
pub mod mundo;
pub mod network;
pub mod pet;
pub mod services;
pub mod session;
pub mod social;
pub mod state;
pub mod stigma;
pub mod teleport;
pub mod tester;
pub mod title;
pub mod trade;
pub mod web_services;
pub mod world;

use crossbeam_channel::Sender;
use data_loader::GameData;
use db::Db;
pub use engine_loop::{ClientUpdate, Connection, Deserialise, Messages, Serialise, ServerUpdate, TICK_RATE, game_update};
use state::State;
use std::collections::HashMap;
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::thread::spawn;
use std::time::Duration;

use error::Error;
use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct RatesConfig {
    #[serde(default = "default_rate")]
    pub xp: f32,
    #[serde(default = "default_rate")]
    pub quest_xp: f32,
    #[serde(default = "default_rate")]
    pub drop: f32,
    #[serde(default = "default_rate")]
    pub kinah: f32,
    #[serde(default = "default_rate")]
    pub ap_player: f32,
    #[serde(default = "default_rate")]
    pub ap_npc: f32,
    #[serde(default = "default_rate")]
    pub craft_xp: f32,
    #[serde(default = "default_rate")]
    pub gather_xp: f32,
}

fn default_rate() -> f32 {
    1.0
}

impl Default for RatesConfig {
    fn default() -> Self {
        Self {
            xp: 1.0,
            quest_xp: 1.0,
            drop: 1.0,
            kinah: 1.0,
            ap_player: 1.0,
            ap_npc: 1.0,
            craft_xp: 1.0,
            gather_xp: 1.0,
        }
    }
}

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
    #[serde(default)]
    pub rates: RatesConfig,
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
            rates: RatesConfig::default(),
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
    let mut cfg = GameServerConfig::default();

    // 1. Prioriza config/gameserver.properties
    let properties_candidates = [
        "config/gameserver.properties",
        "../Produto Final/config/gameserver.properties",
        "../../Produto Final/config/gameserver.properties",
        "gameserver.properties",
    ];

    for prop_path in properties_candidates {
        if std::path::Path::new(prop_path).exists() {
            if let Ok(props) = commons::Properties::load_from_file(prop_path) {
                println!("INFO: Loaded Game config from {prop_path} (.properties)");
                cfg.network.bind_address = props.get_string("gameserver.network.bind.address", &cfg.network.bind_address);
                cfg.network.port = props.get_u16("gameserver.network.port", cfg.network.port);
                cfg.server.server_id = props.get_u8("gameserver.server.id", cfg.server.server_id);
                cfg.server.server_name = props.get_string("gameserver.server.name", &cfg.server.server_name);
                let max_p = props.get_u32("gameserver.server.max.players", cfg.server.max_players);
                cfg.server.max_players = max_p;
                cfg.network.max_players = max_p;
                cfg.network.nio_threads = props.get_u32("gameserver.network.nio.threads", cfg.network.nio_threads);
                cfg.network.processor_threads_min = props.get_u32("gameserver.network.processor.threads.min", cfg.network.processor_threads_min);
                cfg.network.processor_threads_max = props.get_u32("gameserver.network.processor.threads.max", cfg.network.processor_threads_max);
                cfg.network.processor_threshold_kill = props.get_u32("gameserver.network.processor.threshold.kill", cfg.network.processor_threshold_kill);
                cfg.network.processor_threshold_spawn = props.get_u32("gameserver.network.processor.threshold.spawn", cfg.network.processor_threshold_spawn);
                cfg.network.display_unknown_packets = props.get_bool("gameserver.network.display.unknown.packets", cfg.network.display_unknown_packets);
                cfg.network.display_packets = props.get_bool("gameserver.network.display.packets", cfg.network.display_packets);

                cfg.inter_server.login_server_address = props.get_string("gameserver.login.address", &cfg.inter_server.login_server_address);
                cfg.inter_server.gameserver_password = props.get_string("gameserver.login.password", &cfg.inter_server.gameserver_password);
                cfg.inter_server.chat_server_address = props.get_string("gameserver.chat.address", &cfg.inter_server.chat_server_address);
                cfg.inter_server.chat_password = props.get_string("gameserver.chat.password", &cfg.inter_server.chat_password);

                cfg.database.database_path = props.get_string("gameserver.database.path", &cfg.database.database_path);
                cfg.world.data_dir = props.get_string("gameserver.data.dir", &cfg.world.data_dir);
                cfg.world.spawns_file = props.get_string("gameserver.spawns.file", &cfg.world.spawns_file);
                cfg.world.initial_kit_file = props.get_string("gameserver.initial.kit.file", &cfg.world.initial_kit_file);

                cfg.gameplay.country_code = props.get_u8("gameserver.country.code", cfg.gameplay.country_code);
                cfg.gameplay.chat_server_enable = props.get_bool("gameserver.chat.enable", cfg.gameplay.chat_server_enable);
                cfg.gameplay.display_revision = props.get_bool("gameserver.display.revision", cfg.gameplay.display_revision);
                cfg.gameplay.character_limit_count = props.get_u8("gameserver.character.limit.count", cfg.gameplay.character_limit_count);
                cfg.gameplay.character_creation_mode = props.get_u8("gameserver.character.creation.mode", cfg.gameplay.character_creation_mode);
                cfg.gameplay.players_max_level = props.get_u8("gameserver.players.max.level", cfg.gameplay.players_max_level);
                cfg.gameplay.character_name_pattern = props.get_string("gameserver.character.name.pattern", &cfg.gameplay.character_name_pattern);
                cfg.gameplay.character_reentry_time_secs = props.get_u32("gameserver.character.reentry.time.secs", cfg.gameplay.character_reentry_time_secs);

                cfg.rates.xp = props.get_f32("gameserver.rate.xp", cfg.rates.xp);
                cfg.rates.quest_xp = props.get_f32("gameserver.rate.quest.xp", cfg.rates.quest_xp);
                cfg.rates.drop = props.get_f32("gameserver.rate.drop", cfg.rates.drop);
                cfg.rates.kinah = props.get_f32("gameserver.rate.kinah", cfg.rates.kinah);
                cfg.rates.ap_player = props.get_f32("gameserver.rate.ap.player", cfg.rates.ap_player);
                cfg.rates.ap_npc = props.get_f32("gameserver.rate.ap.npc", cfg.rates.ap_npc);
                cfg.rates.craft_xp = props.get_f32("gameserver.rate.craft.xp", cfg.rates.craft_xp);
                cfg.rates.gather_xp = props.get_f32("gameserver.rate.gather.xp", cfg.rates.gather_xp);

                return cfg;
            }
        }
    }

    // 2. Fallback para config/launcher.json
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
            if let Ok(c) = toml::from_str::<GameServerConfig>(&content) {
                println!("INFO: Loaded Game config from {path}");
                return c;
            }
        }
    }

    println!("INFO: Using default Game config");
    cfg
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
    message::set_packet_logging_flags(
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
    spawn(move || engine_loop::game_update(connections, server_rx, db, gd));

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

