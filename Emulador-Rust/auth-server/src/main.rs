mod db;
mod error;
mod gameforge;

use std::io::{Read, Write};
use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::sync::Arc;
use std::thread::spawn;

use db::AuthDb;
use error::Result;
use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct AuthConfig {
    #[serde(default)]
    pub network: NetworkConfig,
    #[serde(default)]
    pub database: DatabaseConfig,
    #[serde(default)]
    pub accounts: AccountsConfig,
    #[serde(default)]
    pub game_servers: GameServersConfig,
    #[serde(default)]
    pub gameforge_pipe: GameforgePipeConfig,
}

#[derive(Debug, Deserialize, Clone)]
pub struct NetworkConfig {
    #[serde(default = "default_bind_address")]
    pub bind_address: String,
    #[serde(default = "default_client_port")]
    pub client_port: u16,
    #[serde(default = "default_hq_port")]
    pub hq_port: u16,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            bind_address: default_bind_address(),
            client_port: default_client_port(),
            hq_port: default_hq_port(),
        }
    }
}

fn default_bind_address() -> String {
    "0.0.0.0".to_string()
}
fn default_client_port() -> u16 {
    2106
}
fn default_hq_port() -> u16 {
    13001
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
pub struct AccountsConfig {
    #[serde(default = "default_true")]
    pub auto_create_accounts: bool,
    #[serde(default = "default_true")]
    pub development_mode: bool,
    #[serde(default = "default_dev_username")]
    pub default_dev_username: String,
}

impl Default for AccountsConfig {
    fn default() -> Self {
        Self {
            auto_create_accounts: true,
            development_mode: true,
            default_dev_username: default_dev_username(),
        }
    }
}

fn default_true() -> bool {
    true
}
fn default_dev_username() -> String {
    "teste".to_string()
}

#[derive(Debug, Deserialize, Clone)]
pub struct GameServersConfig {
    #[serde(default = "default_server_id_val")]
    pub default_server_id: u8,
    #[serde(default = "default_game_server_ip")]
    pub game_server_ip: String,
    #[serde(default = "default_game_server_port")]
    pub game_server_port: u16,
}

impl Default for GameServersConfig {
    fn default() -> Self {
        Self {
            default_server_id: default_server_id_val(),
            game_server_ip: default_game_server_ip(),
            game_server_port: default_game_server_port(),
        }
    }
}

fn default_server_id_val() -> u8 {
    23
}
fn default_game_server_ip() -> String {
    "127.0.0.1".to_string()
}
fn default_game_server_port() -> u16 {
    7777
}

#[derive(Debug, Deserialize, Clone)]
pub struct GameforgePipeConfig {
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default = "default_pipe_name")]
    pub pipe_name: String,
}

impl Default for GameforgePipeConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            pipe_name: default_pipe_name(),
        }
    }
}

fn default_pipe_name() -> String {
    "\\\\.\\pipe\\GameforgeClientJSONRPC".to_string()
}

fn load_config() -> AuthConfig {
    let candidates = [
        "config/auth_server.toml",
        "../config/auth_server.toml",
        "auth_server.toml",
    ];

    for path in candidates {
        if let Ok(content) = std::fs::read_to_string(path) {
            if let Ok(cfg) = toml::from_str::<AuthConfig>(&content) {
                println!("INFO: Loaded Auth config from {path}");
                return cfg;
            }
        }
    }

    println!("INFO: Using default Auth config");
    AuthConfig {
        network: NetworkConfig::default(),
        database: DatabaseConfig::default(),
        accounts: AccountsConfig::default(),
        game_servers: GameServersConfig::default(),
        gameforge_pipe: GameforgePipeConfig::default(),
    }
}

fn main() {
    println!("INFO: Starting Auth Server");
    let config = Arc::new(load_config());

    let db = Arc::new(
        AuthDb::open(&config.database.database_path).expect("failed to open Auth SQLite db"),
    );
    println!("INFO: Opened Auth DB at {}", config.database.database_path);

    // Start internal Gameforge Named Pipe provider if enabled
    if config.gameforge_pipe.enabled {
        gameforge::start_pipe_server(config.accounts.default_dev_username.clone(), db.clone());
    }

    let ports = [config.network.hq_port, config.network.client_port];
    for port in ports {
        let bind_addr = format!("{}:{port}", config.network.bind_address);
        match TcpListener::bind(&bind_addr) {
            Ok(listener) => {
                println!("INFO: Listening on {}", listener.local_addr().unwrap());
                let config = config.clone();
                let db = db.clone();
                spawn(move || {
                    while let Ok((stream, _)) = listener.accept() {
                        let config = config.clone();
                        let db = db.clone();
                        spawn(move || {
                            if let Err(e) = handle(stream, &config, &db) {
                                println!("ERROR: auth session failed: {e}");
                            }
                        });
                    }
                });
            }
            Err(e) => {
                eprintln!("ERROR: Failed to bind to {bind_addr}: {e}");
            }
        }
    }

    // Keep main thread alive
    loop {
        std::thread::sleep(std::time::Duration::from_secs(3600));
    }
}

// ---------------------------------------------------------------------------
// Protocol constants
// ---------------------------------------------------------------------------

const AUTH_GREETING: [u8; 92] = [
    0x5c, 0x00, 0x05, 0x00, 0x00, 0x00,
    // auth_key_1: "5B4503FA-8521-4608-BB60-5CFAC87BD63A"
    0x35, 0x42, 0x34, 0x35, 0x30, 0x33, 0x46, 0x41, 0x2d, 0x38, 0x35, 0x32,
    0x31, 0x2d, 0x34, 0x36, 0x30, 0x38, 0x2d, 0x42, 0x42, 0x36, 0x30, 0x2d,
    0x35, 0x43, 0x46, 0x41, 0x43, 0x38, 0x37, 0x42, 0x44, 0x36, 0x33, 0x41,
    0x00,
    // auth_key_2: "7282405F-79E5-49C2-9872-D4F3CC961FF3"
    0x37, 0x32, 0x38, 0x32, 0x34, 0x30, 0x35, 0x46, 0x2d, 0x37, 0x39, 0x45,
    0x35, 0x2d, 0x34, 0x39, 0x43, 0x32, 0x2d, 0x39, 0x38, 0x37, 0x32, 0x2d,
    0x44, 0x34, 0x46, 0x33, 0x43, 0x43, 0x39, 0x36, 0x31, 0x46, 0x46, 0x33,
    0x00,
    // service name: "aiongfc"
    0x61, 0x69, 0x6f, 0x6e, 0x67, 0x66, 0x63, 0x00,
    // trailer
    0x14, 0x0c, 0x00, 0x00,
];

const ACCOUNT_ID: u32 = 0x0000_0000;
const LOGIN_OK_KEY: u32 = 0x0262_cab6;
const SESSION_TRAILER: u32 = 0x0000_0AD6;

fn login_ok() -> [u8; 14] {
    let mut bytes = [0u8; 14];
    let len = bytes.len() as u16;
    bytes[0..2].copy_from_slice(&len.to_le_bytes());
    bytes[2] = 0x01;
    bytes[6..10].copy_from_slice(&ACCOUNT_ID.to_le_bytes());
    bytes[10..14].copy_from_slice(&LOGIN_OK_KEY.to_le_bytes());
    bytes
}

fn session_key(server_selection: &[u8], _server_id: u8) -> [u8; 22] {
    let mut bytes = [0u8; 22];
    let len = bytes.len() as u16;
    bytes[0..2].copy_from_slice(&len.to_le_bytes());
    bytes[2] = 0x04;
    if server_selection.len() >= 14 {
        bytes[6..10].copy_from_slice(&server_selection[6..10]);
        bytes[10..14].copy_from_slice(&server_selection[10..14]);
    } else if server_selection.len() >= 10 {
        bytes[6..10].copy_from_slice(&server_selection[6..10]);
        bytes[10..14].copy_from_slice(&LOGIN_OK_KEY.to_le_bytes());
    } else {
        bytes[6..10].copy_from_slice(&ACCOUNT_ID.to_le_bytes());
        bytes[10..14].copy_from_slice(&LOGIN_OK_KEY.to_le_bytes());
    }
    bytes[18..22].copy_from_slice(&SESSION_TRAILER.to_le_bytes());
    bytes
}

// ---------------------------------------------------------------------------
// Game server list
// ---------------------------------------------------------------------------

#[derive(Clone, Copy)]
struct GameServer {
    id: u8,
    ip_addr: Ipv4Addr,
    online: bool,
    port: u16,
    typ: u8,
    characters: u8,
}

impl GameServer {
    const LEN: usize = 63;

    fn serialise(&self) -> [u8; Self::LEN] {
        let mut bytes = [0u8; Self::LEN];

        bytes[0] = 0x01;
        bytes[1] = self.typ;
        bytes[4] = self.online as u8;
        bytes[5] = self.id;
        bytes[9] = self.characters;

        let ip = self.ip_addr.to_string();
        let ip = ip.as_bytes();
        bytes[13..13 + ip.len()].copy_from_slice(ip);

        bytes[53..55].copy_from_slice(&self.port.to_le_bytes());

        if self.typ == 0x4 && self.online {
            bytes[55] = 0x1;
        }

        bytes
    }
}

struct GameServerList {
    last_logged_on: u8,
    servers: Vec<GameServer>,
}

impl GameServerList {
    const SEQUENCE_NUMBER: u8 = 0x02;
    const PREAMBLE_LEN: usize = 8;
    const SUFFIX_LEN: usize = 4;
    const MAX: usize = 20;

    fn new(last_logged_on: u8) -> Self {
        Self {
            last_logged_on,
            servers: Vec::with_capacity(Self::MAX),
        }
    }

    fn insert(&mut self, server: GameServer) {
        if self.servers.len() < Self::MAX {
            self.servers.push(server);
        } else {
            eprintln!("WARN: GameServerList at capacity ({} servers), entry dropped", Self::MAX);
        }
    }

    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = Self::PREAMBLE_LEN;

        for server in &self.servers {
            buf[len..len + GameServer::LEN].copy_from_slice(&server.serialise());
            len += GameServer::LEN;
        }

        buf[len] = self.last_logged_on;
        len += Self::SUFFIX_LEN;

        buf[0..2].copy_from_slice(&(len as u16).to_le_bytes());
        buf[2] = Self::SEQUENCE_NUMBER;
        buf[6..8].copy_from_slice(&(self.servers.len() as u16).to_le_bytes());

        len
    }
}

fn build_server_list(config: &AuthConfig, char_count: u8) -> GameServerList {
    let game_ip: Ipv4Addr = config
        .game_servers
        .game_server_ip
        .parse()
        .unwrap_or(Ipv4Addr::new(127, 0, 0, 1));
    let game_port = config.game_servers.game_server_port;
    let server_id = config.game_servers.default_server_id;

    let mut list = GameServerList::new(server_id);
    list.insert(GameServer {
        id: 0x67,
        ip_addr: game_ip,
        online: false,
        port: game_port,
        typ: 5,
        characters: 0,
    });
    list.insert(GameServer {
        id: server_id,
        ip_addr: game_ip,
        online: true,
        port: game_port,
        typ: 4,
        characters: char_count,
    });
    list.insert(GameServer {
        id: 0x79,
        ip_addr: game_ip,
        online: false,
        port: game_port,
        typ: 5,
        characters: 0,
    });
    list
}

fn selected_server_id(buf: &[u8], default_id: u8) -> u8 {
    if buf.len() > 6 && matches!(buf[6], 0x17 | 0x67 | 0x79) {
        return buf[6];
    }
    default_id
}

// ---------------------------------------------------------------------------
// Per-connection handler
// ---------------------------------------------------------------------------

fn handle(mut stream: TcpStream, config: &AuthConfig, db: &Arc<AuthDb>) -> Result<()> {
    let peer = stream.peer_addr()?;
    println!("INFO: incoming {peer}");

    let mut buf = [0u8; 512];

    // 1. Greet: send auth keys + service name
    stream.write_all(&AUTH_GREETING)?;
    println!("DEBUG: → AUTH_GREETING ({} bytes)", AUTH_GREETING.len());

    // 2. Receive client credentials
    let len = stream.read(&mut buf)?;
    if len == 0 {
        println!("INFO: client closed connection before sending credentials (normal probe/disconnect)");
        return Ok(());
    }
    println!("DEBUG: ← credentials ({len} bytes): {:02X?}", &buf[..len]);

    // Handle account lookup / auto creation
    let username = &config.accounts.default_dev_username;
    let account_id = db
        .get_or_create_account(username, config.accounts.auto_create_accounts)
        .unwrap_or(None)
        .unwrap_or(1);
    let char_count = db.count_characters(account_id);

    // 3. Acknowledge login
    let login_ok = login_ok();
    stream.write_all(&login_ok)?;
    println!("DEBUG: → LOGIN_OK: {:02X?}", login_ok);

    // 4. Send game server list
    let mut gs_buf = [0u8; 2048];
    let server_list = build_server_list(config, char_count);
    let gs_len = server_list.serialise(&mut gs_buf);
    stream.write_all(&gs_buf[..gs_len])?;
    println!("DEBUG: → server list ({gs_len} bytes)");

    // 5. Receive server selection from client
    let len = stream.read(&mut buf)?;
    if len == 0 {
        println!("WARN: client closed connection after server list");
        return Ok(());
    }
    println!("DEBUG: ← server selection ({len} bytes): {:02X?}", &buf[..len]);
    let selected_server_id = selected_server_id(&buf[..len], config.game_servers.default_server_id);
    println!("INFO: selected server id: {selected_server_id}");

    // 6. Send session key
    let session_key = session_key(&buf[..len], selected_server_id);
    stream.write_all(&session_key)?;
    println!("DEBUG: → SESSION_KEY: {:02X?}", session_key);

    // 7. Receive final ack
    let len = stream.read(&mut buf)?;
    println!("DEBUG: ← final ack ({len} bytes): {:02X?}", &buf[..len]);

    println!("INFO: auth complete, closing {peer}");
    Ok(())
}


// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_game_server() {
        // Bytes conferidos contra uma captura real do servidor da Gameforge: entrada do servidor
        // de mundo 0x17, online, com 2 personagens na conta.
        let gs = GameServer {
            id: 0x17,
            ip_addr: "79.110.83.115".parse().unwrap(),
            online: true,
            port: 7777,
            typ: 4,
            characters: 2,
        };

        let mut esperado = [0u8; GameServer::LEN];
        esperado[0] = 0x01;
        esperado[1] = 0x04;
        esperado[4] = 0x01;
        esperado[5] = 0x17;
        esperado[9] = 0x02;
        esperado[13..26].copy_from_slice(b"79.110.83.115");   // ASCII, terminado pelo zero em 26
        esperado[53..55].copy_from_slice(&7777u16.to_le_bytes());
        esperado[55] = 0x01;

        assert_eq!(gs.serialise(), esperado);
    }

    #[test]
    fn test_session_key_bytes14_18_are_zero_for_auth_success() {
        // The client interprets bytes[14..18] as an authorization error code.
        // Zero means success; any non-zero causes "Authorization Error (code)".
        let key = session_key(&[], 0x15);
        assert_eq!(&key[14..18], &[0, 0, 0, 0]);
    }

    #[test]
    fn test_login_ok_carries_account_and_key() {
        let login_ok = login_ok();
        assert_eq!(&login_ok[0..3], &[14, 0, 1]);
        assert_eq!(u32::from_le_bytes(login_ok[6..10].try_into().unwrap()), ACCOUNT_ID);
        assert_eq!(
            u32::from_le_bytes(login_ok[10..14].try_into().unwrap()),
            LOGIN_OK_KEY
        );
    }

    #[test]
    fn test_session_key_reuses_selection_identity() {
        let mut selection = [0u8; 14];
        selection[0..2].copy_from_slice(&14u16.to_le_bytes());
        selection[2] = 0x02;
        selection[6..10].copy_from_slice(&ACCOUNT_ID.to_le_bytes());
        selection[10..14].copy_from_slice(&LOGIN_OK_KEY.to_le_bytes());

        let key = session_key(&selection, 0x15);
        assert_eq!(&key[0..3], &[22, 0, 4]);
        assert_eq!(&key[6..14], &selection[6..14]);
        // Os quatro ultimos bytes reproduzem o que o servidor da Gameforge manda. Antes daqui saia
        // o id do servidor no byte 20, que nao corresponde a nada do que foi observado.
        assert_eq!(&key[18..22], &SESSION_TRAILER.to_le_bytes());
    }

    /// Monta a entrada esperada a partir dos offsets documentados, em vez de um blob de bytes.
    /// O erro que travava o cliente na tela de servidores entrou exatamente por um blob desses:
    /// escrito a mao a partir de um palpite, e depois "confirmado" por um teste que repetia o
    /// mesmo palpite.
    fn entrada_esperada(id: u8, typ: u8, online: bool, chars: u8, ip: &str, port: u16)
        -> [u8; GameServer::LEN]
    {
        let mut e = [0u8; GameServer::LEN];
        e[0] = 0x01;
        e[1] = typ;
        e[4] = online as u8;
        e[5] = id;
        e[9] = chars;
        e[13..13 + ip.len()].copy_from_slice(ip.as_bytes());
        e[53..55].copy_from_slice(&port.to_le_bytes());
        if typ == 0x4 && online {
            e[55] = 0x01;
        }
        e
    }

    fn lista_esperada(ultimo: u8, entradas: &[[u8; GameServer::LEN]]) -> Vec<u8> {
        let total = GameServerList::PREAMBLE_LEN
            + entradas.len() * GameServer::LEN
            + GameServerList::SUFFIX_LEN;
        let mut buf = vec![0u8; total];
        buf[0..2].copy_from_slice(&(total as u16).to_le_bytes());
        buf[2] = GameServerList::SEQUENCE_NUMBER;
        buf[6..8].copy_from_slice(&(entradas.len() as u16).to_le_bytes());
        let mut off = GameServerList::PREAMBLE_LEN;
        for e in entradas {
            buf[off..off + GameServer::LEN].copy_from_slice(e);
            off += GameServer::LEN;
        }
        buf[off] = ultimo;
        buf
    }

    #[test]
    fn test_game_servers_list_single() {
        let mut gsl = GameServerList::new(0x15);
        gsl.insert(GameServer {
            id: 0x15,
            ip_addr: "127.0.0.1".parse().unwrap(),
            online: true,
            port: 7777,
            typ: 4,
            characters: 1,
        });

        let mut buf = [0u8; 2048];
        let len = gsl.serialise(&mut buf);

        let esperado = lista_esperada(
            0x15,
            &[entrada_esperada(0x15, 4, true, 1, "127.0.0.1", 7777)],
        );
        assert_eq!(&buf[..len], esperado.as_slice());
    }

    #[test]
    fn test_game_servers_list_multi() {
        let mut gsl = GameServerList::new(0x15);
        gsl.insert(GameServer {
            id: 0x15,
            ip_addr: "127.0.0.1".parse().unwrap(),
            online: true,
            port: 7777,
            typ: 4,
            characters: 1,
        });
        gsl.insert(GameServer {
            id: 0x67,
            ip_addr: "127.0.0.1".parse().unwrap(),
            online: false,
            port: 7777,
            typ: 5,
            characters: 0,
        });

        let mut buf = [0u8; 2048];
        let len = gsl.serialise(&mut buf);

        let esperado = lista_esperada(
            0x15,
            &[
                entrada_esperada(0x15, 4, true, 1, "127.0.0.1", 7777),
                entrada_esperada(0x67, 5, false, 0, "127.0.0.1", 7777),
            ],
        );
        assert_eq!(&buf[..len], esperado.as_slice());
    }

    /// Uma lista grande tem que continuar declarando o tamanho certo: com o tamanho escrito num
    /// byte so, 20 servidores dariam 1272 bytes e o cliente leria 248.
    #[test]
    fn test_lista_grande_declara_tamanho_u16() {
        let mut gsl = GameServerList::new(0x15);
        for i in 0..20u8 {
            gsl.insert(GameServer {
                id: 0x15 + i,
                ip_addr: "127.0.0.1".parse().unwrap(),
                online: true,
                port: 7777,
                typ: 4,
                characters: 0,
            });
        }
        let mut buf = [0u8; 2048];
        let len = gsl.serialise(&mut buf);
        assert_eq!(len, 8 + 20 * GameServer::LEN + 4);
        assert_eq!(u16::from_le_bytes([buf[0], buf[1]]) as usize, len);
        assert_eq!(u16::from_le_bytes([buf[6], buf[7]]), 20);
    }

    #[test]
    fn test_server_list_capacity_is_capped() {
        let mut gsl = GameServerList::new(0x00);
        for i in 0..GameServerList::MAX + 5 {
            gsl.insert(GameServer {
                id: i as u8,
                ip_addr: Ipv4Addr::new(127, 0, 0, 1),
                online: true,
                port: 7777,
                typ: 4,
                characters: 0,
            });
        }
        assert_eq!(gsl.servers.len(), GameServerList::MAX);
    }
}
