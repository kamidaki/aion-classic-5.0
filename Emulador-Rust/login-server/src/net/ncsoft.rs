use crate::db::AuthDb;
use bytes::BufMut;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

const RSA_MODULUS: [u8; 128] = [
    0x8b, 0x92, 0x1f, 0x6e, 0x22, 0x3d, 0x94, 0x48, 0x7b, 0x04, 0x24, 0x39,
    0x91, 0x31, 0x9c, 0x68, 0x8a, 0xca, 0xeb, 0xbb, 0x8d, 0x51, 0xb8, 0x59,
    0xa3, 0x27, 0x4d, 0x1a, 0x88, 0x05, 0x52, 0x3e, 0x7c, 0x95, 0xb5, 0x3e,
    0x61, 0x8b, 0x83, 0x61, 0x54, 0xef, 0xc7, 0xae, 0x71, 0xeb, 0x4c, 0xd0,
    0xa9, 0xa5, 0x85, 0xb3, 0x0e, 0x60, 0x80, 0x9a, 0x37, 0x8d, 0x71, 0x52,
    0xa0, 0x25, 0x72, 0xb8, 0xb7, 0x1f, 0xef, 0x7b, 0x44, 0x07, 0x63, 0x89,
    0x29, 0xef, 0x54, 0x07, 0x25, 0x5d, 0x30, 0xb3, 0x0e, 0xee, 0x04, 0x55,
    0x63, 0x5b, 0x03, 0x6d, 0x75, 0x16, 0x1c, 0x02, 0x23, 0x32, 0x22, 0x50,
    0x57, 0x95, 0x2e, 0x69, 0x84, 0x78, 0x73, 0x5e, 0x3a, 0x4b, 0x80, 0x6b,
    0x02, 0xbd, 0x6a, 0xa3, 0xd3, 0x98, 0x6c, 0x41, 0x69, 0xb9, 0xb0, 0x2c,
    0x62, 0x19, 0x64, 0x5b, 0x3d, 0xa8, 0x4b, 0x2b,
];

pub async fn run_ncsoft_server(
    bind_addr: &str,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("INFO: [LoginServer-NCSoft] Listening on {}", bind_addr);

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                let db_clone = Arc::clone(&db);
                let ip_clone = announce_ip.clone();
                let def_user = default_user.clone();
                tokio::spawn(async move {
                    handle_ncsoft_client(
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
                eprintln!("WARN: [LoginServer-NCSoft] Accept error: {}", e);
            }
        }
    }
}

async fn handle_ncsoft_client(
    mut socket: TcpStream,
    addr: std::net::SocketAddr,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
) {
    println!("INFO: [LoginServer-NCSoft] Incoming connection from {}", addr);

    let session_id: u32 = rand::random();
    let blowfish_key: [u8; 16] = [
        0x6b, 0x60, 0xcb, 0x5b, 0x82, 0xce, 0x90, 0xb1,
        0xcc, 0x2b, 0x6c, 0x55, 0x6c, 0x6c, 0x6c, 0x6c,
    ];

    // 1. Construct SM_INIT (194 bytes)
    let mut sm_init = vec![0u8; 194];
    sm_init[0] = 0x00; // Opcode SM_INIT
    sm_init[1..5].copy_from_slice(&session_id.to_le_bytes());
    sm_init[5..9].copy_from_slice(&0x0000C621u32.to_le_bytes()); // Protocol revision
    sm_init[9..137].copy_from_slice(&RSA_MODULUS);
    sm_init[149..165].copy_from_slice(&blowfish_key);
    sm_init[168] = 0xFD; // Flag de ativação do x64
    sm_init[169..173].copy_from_slice(&[0x04, 0x05, 0x00, 0x00]); // Versão Classic 4.5

    // Add 2-byte length header
    let mut init_pkt = vec![];
    init_pkt.put_u16_le((sm_init.len() + 2) as u16);
    init_pkt.extend_from_slice(&sm_init);

    if let Err(e) = socket.write_all(&init_pkt).await {
        eprintln!("ERROR: [LoginServer-NCSoft] Failed to send SM_INIT: {}", e);
        return;
    }

    let mut buf = [0u8; 2048];

    // 2. Read CM_LOGIN
    let n = match socket.read(&mut buf).await {
        Ok(n) if n > 2 => n,
        _ => return,
    };

    let mut username = default_user.clone();
    if n > 4 {
        let raw_user = &buf[3..n];
        let null_pos = raw_user.iter().position(|&b| b == 0).unwrap_or(raw_user.len());
        if let Ok(u) = std::str::from_utf8(&raw_user[..null_pos]) {
            let trimmed = u.trim();
            if !trimmed.is_empty() && trimmed.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
                username = trimmed.to_string();
            }
        }
    }

    println!("INFO: [LoginServer-NCSoft] Authentication success for '{}'", username);
    let _ = db.get_or_create_account(&username, auto_create);
    let char_count = db.get_character_count(&username);

    // 3. Send SM_LOGIN_OK (52 bytes)
    let session_key1: u32 = 0x026edf39;
    let mut sm_login_ok = vec![0u8; 52];
    sm_login_ok[0..4].copy_from_slice(&10000001u32.to_le_bytes()); // AccountId
    sm_login_ok[4..8].copy_from_slice(&session_key1.to_le_bytes());
    sm_login_ok[16..20].copy_from_slice(&0x0000003Fu32.to_le_bytes()); // Account Flags
    sm_login_ok[32] = 0xFF; // Assinatura Classic
    sm_login_ok[33] = 0xFE; // Assinatura Classic
    sm_login_ok[48..52].copy_from_slice(&0x00000001u32.to_le_bytes()); // TOS flag

    let mut login_ok_pkt = vec![];
    login_ok_pkt.put_u16_le((sm_login_ok.len() + 3) as u16);
    login_ok_pkt.put_u8(0x03); // Opcode SM_LOGIN_OK
    login_ok_pkt.extend_from_slice(&sm_login_ok);
    let _ = socket.write_all(&login_ok_pkt).await;

    // 4. Send SM_SERVER_LIST (21 bytes per server entry)
    let mut srv_entry = [0u8; 21];
    srv_entry[0] = default_server_id; // Server ID (23 = Atreia)
    let ip_parts: Vec<u8> = announce_ip.split('.').filter_map(|s| s.parse::<u8>().ok()).collect();
    if ip_parts.len() == 4 {
        srv_entry[1..5].copy_from_slice(&ip_parts);
    } else {
        srv_entry[1..5].copy_from_slice(&[192, 168, 3, 184]);
    }
    srv_entry[5..9].copy_from_slice(&(announce_port as u32).to_le_bytes());
    srv_entry[9] = 0; // Age limit
    srv_entry[10] = 1; // PvP
    srv_entry[11..13].copy_from_slice(&0u16.to_le_bytes()); // Online players
    srv_entry[13..15].copy_from_slice(&1000u16.to_le_bytes()); // Max players
    srv_entry[15] = 1; // Status online
    srv_entry[16..20].copy_from_slice(&0x00000401u32.to_le_bytes()); // ServerBits: Bit 10 = Classic
    srv_entry[20] = 2; // Bracket / Country Code (2 = Classic EU)

    let mut srv_list_pkt = vec![];
    let payload_len = 2 + 21 + 2 + 1; // count(1) + lastServer(1) + entry(21) + charCountLen(2) + count(1)
    srv_list_pkt.put_u16_le((payload_len + 3) as u16);
    srv_list_pkt.put_u8(0x04); // Opcode SM_SERVER_LIST
    srv_list_pkt.put_u8(1); // 1 server
    srv_list_pkt.put_u8(default_server_id);
    srv_list_pkt.extend_from_slice(&srv_entry);
    srv_list_pkt.put_u16_le(1); // 1 server count
    srv_list_pkt.put_u8(char_count); // Character count on this server

    let _ = socket.write_all(&srv_list_pkt).await;

    // 5. Read CM_SERVER_SELECT
    let n2 = match socket.read(&mut buf).await {
        Ok(n) if n > 2 => n,
        _ => return,
    };

    let selected_id = if n2 >= 4 { buf[3] } else { default_server_id };
    println!("INFO: [LoginServer-NCSoft] Player selected server ID {}", selected_id);

    // 6. Send SM_PLAY_OK
    let session_key2: u32 = 0x026edf39;
    let _ = db.issue_session(&username, session_key2);
    let mut play_ok_pkt = vec![];
    play_ok_pkt.put_u16_le((8 + 3) as u16);
    play_ok_pkt.put_u8(0x06); // Opcode SM_PLAY_OK
    play_ok_pkt.extend_from_slice(&session_key1.to_le_bytes());
    play_ok_pkt.extend_from_slice(&session_key2.to_le_bytes());
    let _ = socket.write_all(&play_ok_pkt).await;

    println!("INFO: [LoginServer-NCSoft] Handshake complete for user '{}'.", username);
}
