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
    let session_id: u32 = rand::random();
    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Incoming connection from {}",
        session_id, addr
    );

    let mut crypt_engine = LoginCryptEngine::new();
    let rsa_manager = RsaManager::new();

    let blowfish_key: [u8; 16] = [
        0x6b, 0x60, 0xcb, 0x5b, 0x82, 0xce, 0x90, 0xb1,
        0xcc, 0x2b, 0x6c, 0x55, 0x6c, 0x6c, 0x6c, 0x6c,
    ];

    let scrambled_modulus = rsa_manager.get_scrambled_modulus();

    // 1. Construct SM_INIT (192 bytes payload -> 194 bytes with header)
    //
    // Verified against game.dll disassembly:
    //   [0x00]        opcode 0x00
    //   [0x01..0x04]  session_id
    //   [0x05..0x08]  protocol revision 0xC621 (checked at game.dll:0x842213)
    //   [0x09..0x88]  scrambled RSA modulus (128 bytes, read at game.dll:0x84221E)
    //   [0x89..0x93]  zeros (11 bytes padding)
    //   [0x94..0xA3]  Blowfish session key (16 bytes = raw[148..164], read at game.dll:0x84222D!)
    //   [0xA4..0xA7]  zeros (4 bytes)
    //   [0xA8]        = raw[168] = 0x03 (RSA & GG enable flag, checked at game.dll:0x84231B)
    //   [0xA9]        version major = 0x04 (read at game.dll:0x842329)
    //   [0xAA]        version minor = 0x05 (read at game.dll:0x84233E)
    let mut raw_init = vec![0u8; 192];
    raw_init[0] = 0x00; // Opcode SM_INIT
    raw_init[1..5].copy_from_slice(&session_id.to_le_bytes());
    raw_init[5..9].copy_from_slice(&0x0000C621u32.to_le_bytes()); // Protocol revision
    raw_init[9..137].copy_from_slice(scrambled_modulus);
    // Blowfish key at offset 0x94 = index 148 (game.dll:0x84222D -> movups xmm0, [r8 + rdi + 0x94])
    raw_init[148..164].copy_from_slice(&blowfish_key);
    // CRITICAL: 0x03 enables CM_AUTH_GG path in game.dll:0x84231B
    raw_init[168] = 0x03;
    raw_init[169] = 0x04; // version major
    raw_init[170] = 0x05; // version minor

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
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_INIT (194 bytes) [SessionID: 0x{:08X}, Flag: 0x03, Version: 4.5, BF@0x94]",
        session_id, session_id
    );

    // Prepare SM_AUTH_GG response template (Opcode 0x0B, 46 bytes payload -> 58 bytes wire length)
    let mut auth_gg_raw = vec![0u8; 46];
    auth_gg_raw[0] = 0x0B; // Opcode SM_AUTH_GG
    auth_gg_raw[1..5].copy_from_slice(&session_id.to_le_bytes());

    let encrypted_auth_gg = crypt_engine.encrypt_packet(&auth_gg_raw);
    let mut auth_gg_pkt = Vec::with_capacity(encrypted_auth_gg.len() + 2);
    auth_gg_pkt.extend_from_slice(&((encrypted_auth_gg.len() + 2) as u16).to_le_bytes());
    auth_gg_pkt.extend_from_slice(&encrypted_auth_gg);

    let mut current_username = default_user.clone();
    let mut account_id = 1u32;

    let session_key1: u32 = 0x026edf39;
    let session_key2: u32 = rand::random();

    // Helper closure to build and send SM_LOGIN_OK
    async fn send_login_ok(
        socket: &mut TcpStream,
        crypt_engine: &LoginCryptEngine,
        session_id: u32,
        account_id: u32,
        session_key1: u32,
        username: &str,
    ) -> Result<(), std::io::Error> {
        let mut raw = vec![0u8; 78];
        raw[0] = 0x03; // Opcode SM_LOGIN_OK
        raw[1..5].copy_from_slice(&account_id.to_le_bytes()); // offset 0x00 in body
        raw[5..9].copy_from_slice(&session_key1.to_le_bytes()); // offset 0x04 in body
        raw[17..21].copy_from_slice(&0x0000003Fu32.to_le_bytes()); // offset 0x10: Account Flags (0x3F)
        raw[21..25].copy_from_slice(&0x0000003Fu32.to_le_bytes());
        raw[25..29].copy_from_slice(&0x0000003Fu32.to_le_bytes());
        raw[29..33].copy_from_slice(&0x0000003Fu32.to_le_bytes());
        raw[33] = 0xFF; // offset 0x20 in body: Magic Classic Signature
        raw[34] = 0xFE; // offset 0x21 in body: Magic Classic Signature
        raw[49..53].copy_from_slice(&0x00000001u32.to_le_bytes()); // offset 0x30 in body: TOS agreement = 1
        // raw[53..78] is trailing zero padding (25 bytes)

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_LOGIN_OK (78 bytes, Account: '{}', ID: {}, Flags: 0x3F, TOS: 1)",
            session_id, username, account_id
        );
        Ok(())
    }

    // Helper closure to build and send SM_SERVER_LIST
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
        raw.push(3);    // 3 servers
        raw.push(default_server_id);    // Last server ID

        let ip_parts: Vec<u8> = announce_ip
            .split('.')
            .filter_map(|s| s.parse::<u8>().ok())
            .collect();
        let ip_arr: [u8; 4] = if ip_parts.len() == 4 {
            [ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3]]
        } else {
            [127, 0, 0, 1]
        };

        let servers = [
            (1u8, 2u8), // Server 1: Atreia (Bracket 2 - Classic EU)
            (2u8, 1u8), // Server 2: Tahabata (Bracket 1 - NA)
            (3u8, 0u8), // Server 3: Universal (Bracket 0)
        ];

        for &(id, bracket) in &servers {
            let mut srv = [0u8; 21];
            srv[0] = id; // Server ID
            srv[1..5].copy_from_slice(&ip_arr); // Server IP
            srv[5..9].copy_from_slice(&(announce_port as u32).to_le_bytes()); // Port (7777)
            srv[9] = 0; // Age limit
            srv[10] = 1; // PvP
            srv[11..13].copy_from_slice(&0u16.to_le_bytes()); // Online count
            srv[13..15].copy_from_slice(&1000u16.to_le_bytes()); // Max count
            srv[15] = 1; // Status Online (1)
            srv[16..20].copy_from_slice(&0x00000401u32.to_le_bytes()); // ServerBits: Bit 10 = Classic (0x0401)
            srv[20] = bracket; // Bracket (2 = Classic EU)
            raw.extend_from_slice(&srv);
        }

        // Character counts section (3 servers)
        raw.extend_from_slice(&3u16.to_le_bytes());
        raw.push(char_count); // Server 1 char count
        raw.push(0);          // Server 2 char count
        raw.push(0);          // Server 3 char count

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_SERVER_LIST (Opcode 0x04, 3 Servers, Target: {}:{}, Chars: {})",
            session_id, announce_ip, announce_port, char_count
        );
        Ok(())
    }

    // Proactively send SM_AUTH_GG to unblock client UI
    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
    if let Err(e) = socket.write_all(&auth_gg_pkt).await {
        eprintln!(
            "ERROR: [LoginServer-NCSoft] [SESSION-{:08X}] Failed to send SM_AUTH_GG: {}",
            session_id, e
        );
        return;
    }
    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_AUTH_GG (Opcode 0x0B, {} bytes)",
        session_id, auth_gg_pkt.len()
    );

    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Handshake ready. Awaiting user credentials (CM_LOGIN)...",
        session_id
    );

    // Packet reception loop
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

        // Check if raw unencrypted or CM_LOGIN format (168 bytes)
        if payload.len() == 168 || (payload.len() >= 5 && payload[4] == 0x0B) {
            println!(
                "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_LOGIN] Native credentials packet received ({} bytes)",
                session_id, payload.len()
            );

            // Attempt RSA decryption of 128-byte block
            let rsa_block = if payload.len() >= 132 {
                &payload[4..132]
            } else if payload.len() >= 128 {
                &payload[..128]
            } else {
                &payload[..]
            };

            if let Some((user, pass)) = rsa_manager.decrypt_credentials(rsa_block) {
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Decrypted RSA Credentials: User='{}', Pass='{}'",
                    session_id, user, pass
                );
                current_username = user;
            } else if let Some(user) = extract_string_from_payload(&payload) {
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

            let char_count = db.get_character_count(&current_username);
            let _ = send_login_ok(
                &mut socket,
                &crypt_engine,
                session_id,
                account_id,
                session_key1,
                &current_username,
            )
            .await;

            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
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
            continue;
        }

        // Decrypt with Blowfish if not already in plaintext opcode format
        let mut dec_payload = payload.clone();
        let decrypted = crypt_engine.decrypt_packet(&mut dec_payload);
        
        let (active_buf, opcode) = if payload.len() >= 1 && (payload[0] == 0x00 || payload[0] == 0x02 || payload[0] == 0x07 || payload[0] == 0x05 || payload[0] == 0x08 || payload[0] == 0x0B) {
            (&payload, payload[0])
        } else {
            if !decrypted {
                println!(
                    "DEBUG: [LoginServer-NCSoft] [SESSION-{:08X}] Blowfish decrypt checksum mismatch (len: {} bytes)",
                    session_id, dec_payload.len()
                );
            }
            (&dec_payload, dec_payload[0])
        };

        let active_hex: String = active_buf.iter().take(16).map(|b| format!("{:02X} ", b)).collect();
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- Opcode 0x{:02X} (Payload: {}...)",
            session_id, opcode, active_hex.trim()
        );

        match opcode {
            0x07 => {
                // CM_AUTH_GG
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_AUTH_GG] GameGuard verification keepalive",
                    session_id
                );
                let _ = socket.write_all(&auth_gg_pkt).await;
            }
            0x00 | 0x08 | 0x0B => {
                // CM_LOGIN
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_LOGIN] (Opcode 0x{:02X})",
                    session_id, opcode
                );

                let rsa_block = if active_buf.len() >= 132 {
                    &active_buf[4..132]
                } else if active_buf.len() >= 128 {
                    &active_buf[..128]
                } else {
                    active_buf
                };

                if let Some((user, pass)) = rsa_manager.decrypt_credentials(rsa_block) {
                    println!(
                        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Decrypted RSA Credentials: User='{}', Pass='{}'",
                        session_id, user, pass
                    );
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

                let char_count = db.get_character_count(&current_username);
                let _ = send_login_ok(
                    &mut socket,
                    &crypt_engine,
                    session_id,
                    account_id,
                    session_key1,
                    &current_username,
                )
                .await;

                tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
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
            0x05 => {
                // CM_SERVER_LIST request
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_SERVER_LIST] Refresh server list request",
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
            0x0A | 0x0C => {
                // CM_TOS_AGREE / CM_USER_AGREEMENT
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_TOS_AGREE] User Agreement accepted by '{}'",
                    session_id, current_username
                );
                let char_count = db.get_character_count(&current_username);
                let _ = send_login_ok(
                    &mut socket,
                    &crypt_engine,
                    session_id,
                    10000001,
                    session_key1,
                    &current_username,
                )
                .await;
                tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
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
                // CM_PLAY / CM_SERVER_SELECT
                let selected_id = if active_buf.len() > 1 && active_buf[1] > 0 {
                    active_buf[1]
                } else {
                    default_server_id
                };

                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_PLAY] Entering World on Server ID {} for user '{}'",
                    session_id, selected_id, current_username
                );

                // Register session in SQLite db so Game Server validates entry
                let _ = db.issue_session(&current_username, session_key2);

                // Send SM_PLAY_OK (Opcode 0x07 / 0x06)
                let mut play_ok_raw = vec![0u8; 10];
                play_ok_raw[0] = 0x07; // Opcode SM_PLAY_OK
                play_ok_raw[1..5].copy_from_slice(&session_key1.to_le_bytes());
                play_ok_raw[5..9].copy_from_slice(&session_key2.to_le_bytes());
                play_ok_raw[9] = selected_id;

                let enc = crypt_engine.encrypt_packet(&play_ok_raw);
                let mut pkt = Vec::with_capacity(enc.len() + 2);
                pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
                pkt.extend_from_slice(&enc);

                if let Err(e) = socket.write_all(&pkt).await {
                    eprintln!(
                        "ERROR: [LoginServer-NCSoft] [SESSION-{:08X}] Failed to send SM_PLAY_OK: {}",
                        session_id, e
                    );
                    break;
                }

                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_PLAY_OK (Opcode 0x07, SessionKey1: 0x{:08X}, SessionKey2: 0x{:08X}, ServerID: {}). Handshake Complete!",
                    session_id, session_key1, session_key2, selected_id
                );
            }
            _ => {
                println!(
                    "WARN: [LoginServer-NCSoft] [SESSION-{:08X}] Unhandled opcode 0x{:02X} (Payload len: {} bytes)",
                    session_id, opcode, dec_payload.len()
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
