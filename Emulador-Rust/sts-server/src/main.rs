mod db;
mod error;
mod net;

use std::net::{TcpListener, TcpStream};
use std::sync::Arc;
use std::thread::spawn;
use std::time::Duration;

use crate::db::Db;
use crate::error::Error;
use crate::net::Session;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Config {
    #[serde(default)]
    network: NetworkConfig,
    #[serde(default)]
    database: DatabaseConfig,
}

#[derive(Debug, Deserialize)]
struct NetworkConfig {
    #[serde(default = "default_bind_address")]
    bind_address: String,
    #[serde(default = "default_port")]
    port: u16,
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
    6600
}

#[derive(Debug, Deserialize)]
struct DatabaseConfig {
    #[serde(default = "default_db_path")]
    database_path: String,
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

fn load_config() -> Config {
    let candidates = [
        "config/sts_server.toml",
        "../config/sts_server.toml",
        "sts_server.toml",
    ];

    for path in candidates {
        if let Ok(content) = std::fs::read_to_string(path) {
            if let Ok(cfg) = toml::from_str::<Config>(&content) {
                println!("INFO: Loaded STS config from {path}");
                return cfg;
            }
        }
    }

    println!("INFO: Using default STS config");
    Config {
        network: NetworkConfig::default(),
        database: DatabaseConfig::default(),
    }
}

fn main() {
    println!("INFO: Starting STS Server");
    let config = load_config();
    let db = Arc::new(Db::open(&config.database.database_path).expect("failed to open STS db"));
    println!("INFO: Opened shared DB at {}", config.database.database_path);

    let bind_addr = format!("{}:{}", config.network.bind_address, config.network.port);
    let listener = TcpListener::bind(&bind_addr).unwrap();
    println!("INFO: Listening on {}", listener.local_addr().unwrap());

    while let Ok((stream, _)) = listener.accept() {
        let db = db.clone();
        spawn(move || {
            if let Err(e) = handle(stream, db) {
                eprintln!("ERROR: session failed: {e:?}");
            }
        });
    }
}

fn handle(stream: TcpStream, db: Arc<Db>) -> error::Result<()> {
    println!(
        "INFO: new session {}",
        stream.peer_addr().map_err(Error::PeerAddr)?
    );

    stream
        .set_read_timeout(Some(Duration::from_secs(60)))
        .map_err(Error::SetStreamTimeout)?;
    stream
        .set_write_timeout(Some(Duration::from_secs(60)))
        .map_err(Error::SetStreamTimeout)?;

    Session::new(db).handle(stream)
}
