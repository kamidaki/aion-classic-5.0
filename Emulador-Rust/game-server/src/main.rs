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

const DB_PATH: &str = "aion.db";

fn find_data_dir() -> PathBuf {
    if let Ok(dir) = std::env::var("AION_DATA_DIR") {
        let p = PathBuf::from(dir);
        if p.exists() {
            return p;
        }
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
    println!("INFO: Starting Game Server");
    let db = Db::open(DB_PATH).expect("failed to open SQLite db");
    println!("INFO: Opened DB at {DB_PATH}");

    let data_dir = find_data_dir();
    println!("INFO: Loading game data from {}", data_dir.display());
    let game_data = Arc::new({
        let mut gd = GameData::load(&data_dir);
        // A tabela de spawns nao vem do cliente: e gerada da captura por tools/extrai_spawns.py.
        let spawns = std::env::var("AION_SPAWNS")
            .unwrap_or_else(|_| "data/spawns.csv".to_string());
        gd.carrega_spawns(std::path::Path::new(&spawns));
        // O kit inicial tambem nao vem do cliente: e a tabela do player_initial_data.xml da base
        // de referencia, com os ids conferidos contra o catalogo 4.5.
        let kit = std::env::var("AION_ITENS_INICIAIS")
            .unwrap_or_else(|_| "data/itens_iniciais.csv".to_string());
        gd.carrega_itens_iniciais(std::path::Path::new(&kit));
        gd
    });

    // A captura de uma sessao real mostra o cliente indo para o game server na porta 7777, que e
    // tambem a porta que o auth server anuncia na lista. O 8443 que estava aqui vinha de outro
    // caminho (o endereco 104.18.41.168 da Gameforge, interceptado pelo adaptador de loopback) e
    // nao casava com a lista -- o cliente era mandado para 7777 e nao havia ninguem ouvindo.
    let port = std::env::var("AION_GAME_PORT")
        .ok()
        .and_then(|v| v.parse::<u16>().ok())
        .unwrap_or(7777);
    let listener = TcpListener::bind(format!("0.0.0.0:{port}")).unwrap();
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
        .set_read_timeout(Some(Duration::from_millis(1)))
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
