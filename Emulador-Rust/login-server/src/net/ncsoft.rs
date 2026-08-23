use crate::crypto::{LoginCryptEngine, RsaManager};
use crate::db::AuthDb;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

pub async fn run_ncsoft_server(
    bind_addr: &str,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
    security: Arc<crate::security::SecurityManager>,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("INFO: [LoginServer-NCSoft] Listening on {}", bind_addr);

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                let db_clone = Arc::clone(&db);
                let ip_clone = announce_ip.clone();
                let def_user = default_user.clone();
                let sec_clone = Arc::clone(&security);
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
                        sec_clone,
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

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
enum ConnectionState {
    Connected,
    AuthedGg,
    AuthedLogin,
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
    security: Arc<crate::security::SecurityManager>,
) {
    if !security.check_connection(addr.ip()) {
        println!("WARN: [LoginServer-NCSoft] Connection from {} rejected by rate-limiter.", addr);
        return;
    }
    let session_id: u32 = rand::random();
    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Incoming connection from {}",
        session_id, addr
    );

    let mut crypt_engine = LoginCryptEngine::new();
    let rsa_manager = RsaManager::new();

    // Generate random 16-byte Blowfish session key
    let mut blowfish_key = [0u8; 16];
    rand::Rng::fill(&mut rand::thread_rng(), &mut blowfish_key[..]);

    let scrambled_modulus = rsa_manager.get_scrambled_modulus();

    // =========================================================================
    // 1. Construct SM_INIT (Java 2.4 Classic EU standard format)
    // =========================================================================
    // Payload layout:
    // [0x00]        0x00 (Opcode SM_INIT)
    // [0x01..0x05]  session_id (u32 LE)
    // [0x05..0x09]  0x0000C621 (Protocol revision u32 LE)
    // [0x09..0x89]  scrambled_modulus (128 bytes RSA modulus)
    // [0x89..0x99]  zeros (16 bytes = 4 * writeD(0))
    // [0x99..0xA9]  blowfish_key (16 bytes session key)
    // [0xA9..0xAD]  197635 (0x00030403 u32 LE) -> Flag: 0x03, Ver: 4.3
    // [0xAD..0xB1]  2097152 (0x00200000 u32 LE)
    // [0xB1..0xC0]  zeros (15 bytes padding to 192 bytes)
    // =========================================================================
    let mut raw_init = vec![0u8; 192];
    raw_init[0] = 0x00; // Opcode SM_INIT
    raw_init[1..5].copy_from_slice(&session_id.to_le_bytes());
    raw_init[5..9].copy_from_slice(&0x0000C621u32.to_le_bytes());
    raw_init[9..137].copy_from_slice(scrambled_modulus);
    // raw_init[137..153] is 16 bytes zeros
    raw_init[153..169].copy_from_slice(&blowfish_key);
    raw_init[169..173].copy_from_slice(&197635u32.to_le_bytes());
    raw_init[173..177].copy_from_slice(&2097152u32.to_le_bytes());

    let encrypted_init = crypt_engine.encrypt_init(&raw_init, blowfish_key);
    let mut init_pkt = Vec::with_capacity(encrypted_init.len() + 2);
    init_pkt.extend_from_slice(&((encrypted_init.len() + 2) as u16).to_le_bytes());
    init_pkt.extend_from_slice(&encrypted_init);

    if let Err(e) = socket.write_all(&init_pkt).await {
        eprintln!(
            "ERROR: [LoginServer-NCSoft] [SESSION-{:08X}] Failed to send SM_INIT: {}",
            session_id, e
        );
        return;
    }
    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_INIT (194 bytes wire size)",
        session_id
    );

    // =========================================================================
    // Helper closures for server responses
    // =========================================================================

    // SM_AUTH_GG (Opcode 0x0B, 40 bytes unencrypted payload)
    async fn send_auth_gg(
        socket: &mut TcpStream,
        crypt_engine: &LoginCryptEngine,
        session_id: u32,
    ) -> Result<(), std::io::Error> {
        let mut raw = vec![0u8; 40];
        raw[0] = 0x0B; // Opcode SM_AUTH_GG
        raw[1..5].copy_from_slice(&session_id.to_le_bytes());
        // raw[5..21] is 4 * writeD(0) (16 bytes zeros)
        // raw[21..40] is 19 bytes zeros
        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);
        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_AUTH_GG (50 bytes wire size)",
            session_id
        );
        Ok(())
    }

    // SM_LOGIN_OK (Opcode 0x03, 68 bytes unencrypted payload)
    async fn send_login_ok(
        socket: &mut TcpStream,
        crypt_engine: &LoginCryptEngine,
        session_id: u32,
        account_id: u32,
        login_ok: u32,
        username: &str,
    ) -> Result<(), std::io::Error> {
        let mut raw = vec![0u8; 68];
        raw[0] = 0x03; // Opcode SM_LOGIN_OK
        raw[1..5].copy_from_slice(&account_id.to_le_bytes());
        raw[5..9].copy_from_slice(&login_ok.to_le_bytes());
        // raw[9..17] is 2 * writeD(0) (8 bytes zeros)
        raw[17..21].copy_from_slice(&1002u32.to_le_bytes());
        // Hex bytes: E4C85FEB000000000000000000000000000000000000000000000000000000004E5464454D6A52424F6A59ACC02BB3314F446C (47 bytes)
        let magic_hex: [u8; 47] = [
            0xE4, 0xC8, 0x5F, 0xEB, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x4E, 0x54, 0x64, 0x45, 0x4D, 0x6A, 0x52, 0x42, 0x4F, 0x6A, 0x59, 0xAC, 0xC0, 0x2B, 0xB3,
        ];
        raw[21..68].copy_from_slice(&magic_hex);

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_LOGIN_OK (74 bytes wire size, Account: '{}', ID: {})",
            session_id, username, account_id
        );
        Ok(())
    }

    // SM_SERVER_LIST (Opcode 0x04)
    async fn send_server_list(
        socket: &mut TcpStream,
        crypt_engine: &LoginCryptEngine,
        session_id: u32,
        announce_ip: &str,
        announce_port: u16,
        default_server_id: u8,
        char_count: u8,
    ) -> Result<(), std::io::Error> {
        let mut raw = Vec::new();
        raw.push(0x04); // Opcode SM_SERVER_LIST
        raw.push(1);    // 1 Server in list
        raw.push(default_server_id); // Last server ID

        let ip_parts: Vec<u8> = announce_ip
            .split('.')
            .filter_map(|s| s.parse::<u8>().ok())
            .collect();
        let ip_arr: [u8; 4] = if ip_parts.len() == 4 {
            [ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3]]
        } else {
            [127, 0, 0, 1]
        };

        // Server 1 entry
        raw.push(default_server_id); // Server ID (1)
        raw.extend_from_slice(&ip_arr); // Server IP (4 bytes)
        raw.extend_from_slice(&(announce_port as u32).to_le_bytes()); // Port (4 bytes)
        raw.push(0); // Age limit = 0
        raw.push(1); // PvP = 1
        raw.extend_from_slice(&0u16.to_le_bytes()); // Current players = 0
        raw.extend_from_slice(&1000u16.to_le_bytes()); // Max players = 1000
        raw.push(1); // Server Status Up = 1
        raw.push(0); // Brackets = 0
        raw.extend_from_slice(&4u32.to_le_bytes()); // ServerBits: 4 (Classic)

        // Character count section
        let max_id = default_server_id as u16;
        raw.extend_from_slice(&(max_id + 1).to_le_bytes());
        raw.push(0x01);

        for i in 1..=max_id {
            if i == (default_server_id as u16) {
                raw.push(char_count);
            } else {
                raw.push(0);
            }
        }
        // 15 bytes Classic NA/EU padding
        raw.extend_from_slice(&[0u8; 15]);

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_SERVER_LIST (Opcode 0x04, Target: {}:{}, Chars: {})",
            session_id, announce_ip, announce_port, char_count
        );
        Ok(())
    }

    // SM_PLAY_OK (Opcode 0x07, 24 bytes unencrypted payload)
    async fn send_play_ok(
        socket: &mut TcpStream,
        crypt_engine: &LoginCryptEngine,
        session_id: u32,
        play_ok1: u32,
        play_ok2: u32,
        server_id: u8,
    ) -> Result<(), std::io::Error> {
        let mut raw = vec![0u8; 24];
        raw[0] = 0x07; // Opcode SM_PLAY_OK
        raw[1..5].copy_from_slice(&play_ok1.to_le_bytes());
        raw[5..9].copy_from_slice(&play_ok2.to_le_bytes());
        raw[9] = server_id;
        // raw[10..24] is 14 bytes zeros

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_PLAY_OK (Opcode 0x07, PlayOk1: 0x{:08X}, PlayOk2: 0x{:08X}, ServerID: {})",
            session_id, play_ok1, play_ok2, server_id
        );
        Ok(())
    }

    let mut state = ConnectionState::Connected;
    let mut current_username = default_user.clone();
    let mut account_id = 1u32;
    let login_ok: u32 = 0x026edf39;
    let play_ok1: u32 = 0x026edf39;
    let play_ok2: u32 = rand::random();

    // =========================================================================
    // 2. Packet Reception Loop
    // =========================================================================
    let mut header_buf = [0u8; 2];
    loop {
        match socket.read_exact(&mut header_buf).await {
            Ok(_) => {}
            Err(e) => {
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Connection closed by client: {}",
                    session_id, e
                );
                break;
            }
        }

        let pkt_len = u16::from_le_bytes(header_buf) as usize;
        if pkt_len < 2 || pkt_len > 8192 {
            eprintln!(
                "WARN: [LoginServer-NCSoft] [SESSION-{:08X}] Invalid packet length: {} bytes. Disconnecting.",
                session_id, pkt_len
            );
            break;
        }

        let payload_len = pkt_len - 2;
        let mut payload = vec![0u8; payload_len];
        if let Err(e) = socket.read_exact(&mut payload).await {
            eprintln!(
                "ERROR: [LoginServer-NCSoft] [SESSION-{:08X}] Failed to read packet payload ({} bytes): {}",
                session_id, payload_len, e
            );
            break;
        }

        let raw_hex: String = payload.iter().take(16).map(|b| format!("{:02X} ", b)).collect();
        println!(
            "DEBUG: [LoginServer-NCSoft] [SESSION-{:08X}] <- Received {} bytes (Raw: {}...)",
            session_id, pkt_len, raw_hex.trim()
        );

        // Decrypt with Blowfish session key
        let mut dec_payload = payload.clone();
        let decrypted = crypt_engine.decrypt_packet(&mut dec_payload);
        let active_buf = if decrypted {
            &dec_payload
        } else {
            &payload
        };

        let opcode = if !active_buf.is_empty() { active_buf[0] } else { 0xFF };
        let active_hex: String = active_buf.iter().take(16).map(|b| format!("{:02X} ", b)).collect();
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- Opcode 0x{:02X} (State: {:?}, Decrypted: {}, Len: {} bytes, Body: {}...)",
            session_id, opcode, state, decrypted, active_buf.len(), active_hex.trim()
        );

        match opcode {
            0x07 => {
                // CM_AUTH_GG
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_AUTH_GG] GameGuard handshake request",
                    session_id
                );
                state = ConnectionState::AuthedGg;
                let _ = send_auth_gg(&mut socket, &crypt_engine, session_id).await;
            }
            0x08 => {
                // CM_UPDATE_SESSION
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_UPDATE_SESSION]",
                    session_id
                );
            }
            0x0B | 0x12 | 0x00 => {
                // CM_LOGIN (Opcode 0x0B) / CM_NP_LOGIN (Opcode 0x12)
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_LOGIN] (Opcode 0x{:02X}, {} bytes)",
                    session_id, opcode, active_buf.len()
                );

                let mut resolved_user = None;
                // Scan for 128-byte RSA block at common offsets
                for &offset in &[1, 4, 5, 8, 12, 0] {
                    if active_buf.len() >= offset + 128 {
                        if let Some((user, pass)) = rsa_manager.decrypt_credentials(&active_buf[offset..offset + 128]) {
                            if !user.is_empty() && user.chars().all(|c| c.is_ascii_graphic() || c == ' ') {
                                println!(
                                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Decrypted RSA Credentials at offset {}: User='{}', Pass='{}'",
                                    session_id, offset, user, pass
                                );
                                resolved_user = Some(user);
                                break;
                            }
                        }
                    }
                }

                if resolved_user.is_none() && decrypted {
                    for &offset in &[1, 4, 5, 8, 12, 0] {
                        if payload.len() >= offset + 128 {
                            if let Some((user, pass)) = rsa_manager.decrypt_credentials(&payload[offset..offset + 128]) {
                                if !user.is_empty() && user.chars().all(|c| c.is_ascii_graphic() || c == ' ') {
                                    println!(
                                        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Decrypted RSA Credentials in raw payload at offset {}: User='{}', Pass='{}'",
                                        session_id, offset, user, pass
                                    );
                                    resolved_user = Some(user);
                                    break;
                                }
                            }
                        }
                    }
                }

                if let Some(user) = resolved_user {
                    current_username = user;
                } else if let Some(user) = extract_string_from_payload(active_buf) {
                    current_username = user;
                }

                let acc = db.get_or_create_account(&current_username, auto_create);
                account_id = match acc {
                    Ok(Some(a)) => (a.id as u32).max(1),
                    _ => 1,
                };

                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Authenticated Account: '{}' (ID: {}, Auto-Created: {})",
                    session_id, current_username, account_id, auto_create
                );

                state = ConnectionState::AuthedLogin;
                let _ = send_login_ok(
                    &mut socket,
                    &crypt_engine,
                    session_id,
                    account_id,
                    login_ok,
                    &current_username,
                )
                .await;
            }
            0x05 => {
                // CM_SERVER_LIST
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_SERVER_LIST] Requesting Server List",
                    session_id
                );
                let char_count = db.get_character_count(&current_username);
                let _ = send_server_list(
                    &mut socket,
                    &crypt_engine,
                    session_id,
                    &announce_ip,
                    announce_port,
                    default_server_id,
                    char_count,
                )
                .await;
            }
            0x02 => {
                // CM_PLAY
                let selected_id = if active_buf.len() > 8 && active_buf[8] > 0 {
                    active_buf[8]
                } else if active_buf.len() > 1 && active_buf[1] > 0 {
                    active_buf[1]
                } else {
                    default_server_id
                };

                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_PLAY] Entering World on Server ID {} for user '{}'",
                    session_id, selected_id, current_username
                );

                // Register session in SQLite db for GameServer validation
                let _ = db.issue_session(account_id, &current_username, play_ok2);

                let _ = send_play_ok(
                    &mut socket,
                    &crypt_engine,
                    session_id,
                    play_ok1,
                    play_ok2,
                    selected_id,
                )
                .await;
            }
            _ => {
                println!(
                    "WARN: [LoginServer-NCSoft] [SESSION-{:08X}] Unhandled opcode 0x{:02X} (Len: {} bytes)",
                    session_id, opcode, active_buf.len()
                );
            }
        }
    }
}

fn extract_string_from_payload(payload: &[u8]) -> Option<String> {
    for start in 1..payload.len().saturating_sub(3) {
        let slice = &payload[start..];
        let null_pos = slice.iter().position(|&b| b == 0).unwrap_or(slice.len());
        if null_pos >= 3 && null_pos <= 32 {
            if let Ok(s) = std::str::from_utf8(&slice[..null_pos]) {
                let trimmed = s.trim();
                if !trimmed.is_empty()
                    && trimmed
                        .chars()
                        .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
                {
                    return Some(trimmed.to_string());
                }
            }
        }
    }
    None
}
