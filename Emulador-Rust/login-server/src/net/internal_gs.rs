use crate::config::LoginServerConfig;
use crate::db::AuthDb;
use parking_lot::RwLock;
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::Instant;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

#[derive(Debug, Clone)]
pub struct ActiveGameServer {
    pub server_id: u8,
    pub ip: String,
    pub port: u16,
    pub max_players: u32,
    pub current_players: u32,
    pub last_heartbeat: Instant,
}

pub type ActiveGameServerRegistry = Arc<RwLock<HashMap<u8, ActiveGameServer>>>;

pub fn new_registry() -> ActiveGameServerRegistry {
    Arc::new(RwLock::new(HashMap::new()))
}

pub async fn start_internal_gs_listener(
    cfg: LoginServerConfig,
    db: Arc<AuthDb>,
    registry: ActiveGameServerRegistry,
) {
    let bind_addr = format!("0.0.0.0:{}", cfg.gameserver_port);
    let listener = match TcpListener::bind(&bind_addr).await {
        Ok(l) => {
            println!(
                "INFO: [LoginServer-InternalGS] Inter-server TCP listener online on {} (Auth Port: {})",
                bind_addr, cfg.gameserver_port
            );
            l
        }
        Err(e) => {
            eprintln!(
                "ERROR: [LoginServer-InternalGS] Failed to bind internal port {}: {}",
                cfg.gameserver_port, e
            );
            return;
        }
    };

    loop {
        match listener.accept().await {
            Ok((socket, peer_addr)) => {
                let db_clone = db.clone();
                let cfg_clone = cfg.clone();
                let registry_clone = registry.clone();
                tokio::spawn(async move {
                    handle_gameserver_client(socket, peer_addr, cfg_clone, db_clone, registry_clone).await;
                });
            }
            Err(e) => {
                eprintln!("WARN: [LoginServer-InternalGS] Accept error: {}", e);
            }
        }
    }
}

async fn handle_gameserver_client(
    mut socket: TcpStream,
    peer_addr: SocketAddr,
    cfg: LoginServerConfig,
    db: Arc<AuthDb>,
    registry: ActiveGameServerRegistry,
) {
    println!(
        "INFO: [LoginServer-InternalGS] Incoming inter-server connection from GameServer at {}",
        peer_addr
    );

    let mut header = [0u8; 2];
    if socket.read_exact(&mut header).await.is_err() {
        return;
    }
    let len = u16::from_le_bytes(header) as usize;
    if len < 3 || len > 2048 {
        return;
    }

    let mut payload = vec![0u8; len - 2];
    if socket.read_exact(&mut payload).await.is_err() {
        return;
    }

    let opcode = payload[0];
    if opcode != 0x01 {
        eprintln!(
            "WARN: [LoginServer-InternalGS] GameServer from {} sent unexpected initial opcode 0x{:02X}",
            peer_addr, opcode
        );
        return;
    }

    // CM_GS_AUTH parser:
    // [0] = 0x01
    // [1] = server_id: u8
    // [2..4] = port: u16
    // [4..8] = max_players: u32
    // [8..10] = password_len: u16
    // [10..10+len] = password string
    if payload.len() < 10 {
        eprintln!("WARN: [LoginServer-InternalGS] Malformed CM_GS_AUTH payload from {}", peer_addr);
        return;
    }

    let server_id = payload[1];
    let port = u16::from_le_bytes([payload[2], payload[3]]);
    let max_players = u32::from_le_bytes([payload[4], payload[5], payload[6], payload[7]]);
    let pass_len = u16::from_le_bytes([payload[8], payload[9]]) as usize;

    if payload.len() < 10 + pass_len {
        eprintln!("WARN: [LoginServer-InternalGS] CM_GS_AUTH password length out of bounds from {}", peer_addr);
        return;
    }

    let password = String::from_utf8_lossy(&payload[10..10 + pass_len]).to_string();
    let gs_ip = peer_addr.ip().to_string();

    // Validação de senha: bate com launcher.json ou com a tabela gameservers do banco de dados
    let mut authed = password == cfg.gameserver_password;
    if !authed {
        if let Ok(servers) = db.get_game_servers() {
            if let Some(srv) = servers.iter().find(|s| s.id == server_id) {
                if srv.password == password {
                    authed = true;
                }
            }
        }
    }

    if !authed {
        eprintln!(
            "ERROR: [LoginServer-InternalGS] GameServer #{} from {} REJECTED: Invalid password (Got: '{}', Expected: '{}')",
            server_id, peer_addr, password, cfg.gameserver_password
        );
        // Envia SM_GS_AUTH_RESPONSE (Status 1 = REJECTED)
        let resp = [0x04, 0x00, 0x01, 0x01]; // len=4, opcode=0x01, status=1
        let _ = socket.write_all(&resp).await;
        return;
    }

    // Sucesso na autenticação
    println!(
        "INFO: [LoginServer-InternalGS] GameServer #{} AUTHENTICATED SUCCESSFULLY! (IP: {}, Port: {}, MaxPlayers: {})",
        server_id, gs_ip, port, max_players
    );

    // Registra o GameServer como ativo na memória
    {
        let mut reg = registry.write();
        reg.insert(
            server_id,
            ActiveGameServer {
                server_id,
                ip: if gs_ip == "127.0.0.1" || gs_ip == "::1" {
                    cfg.announce_game_server_ip.clone()
                } else {
                    gs_ip.clone()
                },
                port,
                max_players,
                current_players: 0,
                last_heartbeat: Instant::now(),
            },
        );
    }

    // Envia SM_GS_AUTH_RESPONSE (Status 0 = AUTHED)
    let resp = [0x04, 0x00, 0x01, 0x00];
    if socket.write_all(&resp).await.is_err() {
        return;
    }

    // Loop de controle e heartbeat do GameServer
    loop {
        if socket.read_exact(&mut header).await.is_err() {
            break;
        }
        let pkt_len = u16::from_le_bytes(header) as usize;
        if pkt_len < 2 || pkt_len > 4096 {
            break;
        }
        let mut body = vec![0u8; pkt_len - 2];
        if socket.read_exact(&mut body).await.is_err() {
            break;
        }

        let op = body[0];
        match op {
            0x02 => {
                // CM_GS_PONG / Heartbeat
                {
                    let mut reg = registry.write();
                    if let Some(s) = reg.get_mut(&server_id) {
                        s.last_heartbeat = Instant::now();
                    }
                }
                // Responde SM_GS_PING
                let pong = [0x04, 0x00, 0x02, 0x00];
                let _ = socket.write_all(&pong).await;
            }
            0x03 => {
                // CM_GS_PLAYER_COUNT
                if body.len() >= 5 {
                    let cur = u32::from_le_bytes([body[1], body[2], body[3], body[4]]);
                    let mut reg = registry.write();
                    if let Some(s) = reg.get_mut(&server_id) {
                        s.current_players = cur;
                        s.last_heartbeat = Instant::now();
                    }
                }
            }
            _ => {}
        }
    }

    // GameServer desconectado: remove da lista ativa
    {
        let mut reg = registry.write();
        reg.remove(&server_id);
    }
    println!(
        "WARN: [LoginServer-InternalGS] GameServer #{} disconnected from LoginServer. Removed from active list.",
        server_id
    );
}
