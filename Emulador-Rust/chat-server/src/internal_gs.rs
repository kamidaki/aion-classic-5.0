use crate::channels::ChannelManager;
use crate::config::ChatServerConfig;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

pub async fn start_internal_gs_listener(
    cfg: ChatServerConfig,
    channel_mgr: Arc<ChannelManager>,
) {
    let bind_addr = format!("0.0.0.0:{}", cfg.internal_port);
    let listener = match TcpListener::bind(&bind_addr).await {
        Ok(l) => {
            println!(
                "INFO: [ChatServer-InternalGS] Inter-server TCP listener online on {} (Auth Port: {})",
                bind_addr, cfg.internal_port
            );
            l
        }
        Err(e) => {
            eprintln!(
                "ERROR: [ChatServer-InternalGS] Failed to bind internal port {}: {}",
                cfg.internal_port, e
            );
            return;
        }
    };

    loop {
        match listener.accept().await {
            Ok((socket, peer_addr)) => {
                let cfg_clone = cfg.clone();
                let mgr_clone = channel_mgr.clone();
                tokio::spawn(async move {
                    handle_gameserver_client(socket, peer_addr, cfg_clone, mgr_clone).await;
                });
            }
            Err(e) => {
                eprintln!("WARN: [ChatServer-InternalGS] Accept error: {}", e);
            }
        }
    }
}

async fn handle_gameserver_client(
    mut socket: TcpStream,
    peer_addr: SocketAddr,
    cfg: ChatServerConfig,
    _channel_mgr: Arc<ChannelManager>,
) {
    println!(
        "INFO: [ChatServer-InternalGS] Incoming inter-server connection from GameServer at {}",
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
            "WARN: [ChatServer-InternalGS] GameServer from {} sent unexpected initial opcode 0x{:02X}",
            peer_addr, opcode
        );
        return;
    }

    // CM_CS_AUTH parser:
    // [0] = 0x01
    // [1] = server_id: u8
    // [2..4] = password_len: u16
    // [4..4+len] = password string
    if payload.len() < 4 {
        eprintln!("WARN: [ChatServer-InternalGS] Malformed CM_CS_AUTH payload from {}", peer_addr);
        return;
    }

    let server_id = payload[1];
    let pass_len = u16::from_le_bytes([payload[2], payload[3]]) as usize;

    if payload.len() < 4 + pass_len {
        eprintln!("WARN: [ChatServer-InternalGS] CM_CS_AUTH password length out of bounds from {}", peer_addr);
        return;
    }

    let password = String::from_utf8_lossy(&payload[4..4 + pass_len]).to_string();

    // Validação de senha: bate com launcher.json
    if password != cfg.chat_password {
        eprintln!(
            "ERROR: [ChatServer-InternalGS] GameServer #{} from {} REJECTED: Invalid password (Got: '{}', Expected: '{}')",
            server_id, peer_addr, password, cfg.chat_password
        );
        // Envia SM_CS_AUTH_RESPONSE (Status 1 = REJECTED)
        let resp = [0x04, 0x00, 0x01, 0x01];
        let _ = socket.write_all(&resp).await;
        return;
    }

    println!(
        "INFO: [ChatServer-InternalGS] GameServer #{} AUTHENTICATED SUCCESSFULLY with ChatServer!",
        server_id
    );

    // Envia SM_CS_AUTH_RESPONSE (Status 0 = AUTHED)
    let resp = [0x04, 0x00, 0x01, 0x00];
    if socket.write_all(&resp).await.is_err() {
        return;
    }

    // Loop de controle
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
                // Heartbeat / Ping
                let pong = [0x04, 0x00, 0x02, 0x00];
                let _ = socket.write_all(&pong).await;
            }
            _ => {}
        }
    }

    println!(
        "WARN: [ChatServer-InternalGS] GameServer #{} disconnected from ChatServer.",
        server_id
    );
}
