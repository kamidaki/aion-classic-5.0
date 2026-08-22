use crate::db::AuthDb;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

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

pub async fn run_hq_server(
    bind_addr: &str,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("INFO: [LoginServer-HQ] Listening on {}", bind_addr);

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                let db_clone = Arc::clone(&db);
                let ip_clone = announce_ip.clone();
                let def_user = default_user.clone();
                tokio::spawn(async move {
                    handle_hq_client(
                        socket,
                        addr,
                        ip_clone,
                        announce_port,
                        default_server_id,
                        db_clone,
                        auto_create,
                        def_user,
                    )
                    .await;
                });
            }
            Err(e) => {
                eprintln!("WARN: [LoginServer-HQ] Accept error: {}", e);
            }
        }
    }
}

async fn handle_hq_client(
    mut socket: TcpStream,
    addr: std::net::SocketAddr,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
) {
    println!("INFO: [LoginServer-HQ] Incoming client connection from {}", addr);

    // 1. Send AUTH_GREETING (92 bytes)
    if let Err(e) = socket.write_all(&AUTH_GREETING).await {
        eprintln!("ERROR: [LoginServer-HQ] Failed to send AUTH_GREETING: {}", e);
        return;
    }

    let mut buf = [0u8; 1024];

    // 2. Read CREDENTIALS
    let n = match socket.read(&mut buf).await {
        Ok(n) if n > 0 => n,
        _ => return,
    };

    // Extract dynamic username from raw payload
    let mut username = default_user.clone();
    if n >= 4 {
        let raw_slice = &buf[3..n];
        let null_pos = raw_slice.iter().position(|&b| b == 0).unwrap_or(raw_slice.len());
        if let Ok(extracted) = std::str::from_utf8(&raw_slice[..null_pos]) {
            let trimmed = extracted.trim();
            if !trimmed.is_empty() && trimmed.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
                username = trimmed.to_string();
            }
        }
    }

    println!("INFO: [LoginServer-HQ] Authentication accepted for user '{}'", username);
    let _ = db.get_or_create_account(&username, auto_create);
    let char_count = db.get_character_count(&username);

    // 3. Send LOGIN_OK (14 bytes)
    let login_key: u32 = 0x026edf39;
    let mut login_ok = vec![0x0e, 0x00, 0x01, 0x00, 0x00, 0x00];
    login_ok.extend_from_slice(&0u32.to_le_bytes()); // account_id
    login_ok.extend_from_slice(&login_key.to_le_bytes()); // login_key
    let _ = socket.write_all(&login_ok).await;

    // 4. Send SERVER_LIST (201 bytes)
    let mut server_list = vec![
        0xc9, 0x00, // length = 201
        0x02, 0x00, 0x00, 0x00, // opcode 0x02
        0x03, 0x00, // 3 servers
    ];

    // Entry 0: Instance server (offline)
    let mut e0 = [0u8; 63];
    e0[0] = 0x01; e0[1] = 0x05; e0[4] = 0x00; e0[5] = 0x67;
    let ip_dummy = b"79.110.83.114\0";
    e0[13..13 + ip_dummy.len()].copy_from_slice(ip_dummy);
    e0[53..55].copy_from_slice(&7777u16.to_le_bytes());
    server_list.extend_from_slice(&e0);

    // Entry 1: Main Game Server (Atreia, Online)
    let mut e1 = [0u8; 63];
    e1[0] = 0x01; e1[1] = 0x04; e1[4] = 0x01; e1[5] = default_server_id;
    e1[9] = char_count;
    let mut ip_bytes = announce_ip.as_bytes().to_vec();
    ip_bytes.push(0);
    let copy_len = ip_bytes.len().min(30);
    e1[13..13 + copy_len].copy_from_slice(&ip_bytes[..copy_len]);
    e1[53..55].copy_from_slice(&announce_port.to_le_bytes());
    e1[55] = 0x01; // Online flag
    server_list.extend_from_slice(&e1);

    // Entry 2: Instance server (offline)
    let mut e2 = [0u8; 63];
    e2[0] = 0x01; e2[1] = 0x05; e2[4] = 0x00; e2[5] = 0x79;
    let ip_dummy2 = b"79.110.83.116\0";
    e2[13..13 + ip_dummy2.len()].copy_from_slice(ip_dummy2);
    e2[53..55].copy_from_slice(&7777u16.to_le_bytes());
    server_list.extend_from_slice(&e2);

    // Trailer
    server_list.extend_from_slice(&[0x00, 0x00, 0x00, 0x00]);
    let _ = socket.write_all(&server_list).await;

    // 5. Read SERVER_SELECT
    let n2 = match socket.read(&mut buf).await {
        Ok(n) if n > 0 => n,
        _ => return,
    };

    let server_id = if n2 >= 10 {
        u32::from_le_bytes(buf[6..10].try_into().unwrap_or([default_server_id, 0, 0, 0]))
    } else {
        default_server_id as u32
    };

    println!("INFO: [LoginServer-HQ] Player selected server ID 0x{:02X}", server_id);

    // 6. Send SESSION_KEY (22 bytes)
    let _ = db.issue_session(&username, login_key);
    let mut session_key_pkt = vec![
        0x16, 0x00, // length = 22
        0x04, 0x00, 0x00, 0x00, // opcode 0x04
    ];
    session_key_pkt.extend_from_slice(&server_id.to_le_bytes());
    session_key_pkt.extend_from_slice(&login_key.to_le_bytes());
    session_key_pkt.extend_from_slice(&[0x00, 0x00, 0x00, 0x00]); // Error code = 0 (MUST BE ZERO)
    session_key_pkt.extend_from_slice(&[0xd6, 0x0a, 0x00, 0x00]); // Extra flag
    let _ = socket.write_all(&session_key_pkt).await;

    println!("INFO: [LoginServer-HQ] Session established for user '{}'. Transitioning to Game Server.", username);
}
