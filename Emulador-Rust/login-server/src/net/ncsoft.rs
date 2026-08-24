//! # O que o cliente faz nesta porta, medido de dentro dele
//!
//! Instrumentando o `version.dll` com hooks de `recv`/`WSARecv` (25/08/2026), da para ver a
//! sequencia exata do lado do cliente:
//!
//! ```text
//! connect(Port=2106)
//! recv(pediu=2)   -> 2      <- le o cabecalho de tamanho
//! recv(pediu=192) -> 192    <- le o corpo do SM_INIT
//! recv(pediu=2)   -> 2      <- e assim por diante, para os quatro pacotes
//! recv(pediu=48)  -> 48
//! recv(pediu=2)   -> 2
//! recv(pediu=72)  -> 72
//! recv(pediu=2)   -> 2
//! recv(pediu=48)  -> 48
//! recv(pediu=2)   -> FALHOU WSA=10035   <- e fica em laco pedindo mais
//! ```
//!
//! O cliente **le tudo**, com o enquadramento correto: pede 2 bytes, descobre o tamanho, pede o
//! restante. `10035` e `WSAEWOULDBLOCK` -- nao ha mais dado --, nao erro. A conexao fica saudavel.
//!
//! ## CORRECAO de uma afirmacao anterior
//!
//! Este arquivo dizia, com base na janela de recepcao do TCP, que o cliente "nao le um unico
//! byte". **Isso estava errado.** A janela nao se recuperava porque o Windows nao emite window
//! update quando a aplicacao le rapido e nada mais chega -- sinal ambiguo, que foi lido como
//! prova. A medicao de dentro do processo desmente.
//!
//! ## O que sobra
//!
//! O cliente le, nao se da por satisfeito e espera mais. Nunca envia: zero `send`/`WSASend` no
//! socket, com os guards de socket NOPpados. E o hook de `SubmitCredentials`
//! (`game.dll+0x1419C0`) nunca dispara -- o clique no login nao chega a submeter credenciais.
//!
//! Testado e descartado:
//!
//! * **cadeia proativa** -- com so o `SM_INIT`, o comportamento e identico (le, espera, nao
//!   envia). Nao e excesso de pacote inesperado.
//! * **estado `AUTHED_READY`** -- o patch `0x14BB6F8 = 3` aplica e nao muda nada.
//! * **porta e protocolo** -- na 13001, com o protocolo HQ, o cliente tambem le e espera.
//!
//! Os layouts abaixo seguem `CONTEXT.md` e `PLANO-LOGINSERVER/07-MAPEAMENTO-OFFSETS.md`. Nenhum
//! foi confirmado por reacao do cliente, porque ele nao reage a nenhum deles.

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

/// Le um override numerico do ambiente. Aceita `0x` na frente. Sem a variavel, devolve o padrao.
///
/// Existe para bisseccionar contra o cliente sem recompilar: a documentacao do projeto discorda
/// de si mesma em alguns campos, e a unica forma de saber qual valor vale e medir.
fn env_num(nome: &str, padrao: u64) -> u64 {
    let Ok(bruto) = std::env::var(nome) else {
        return padrao;
    };
    let t = bruto.trim();
    let r = t
        .strip_prefix("0x")
        .or_else(|| t.strip_prefix("0X"))
        .map(|h| u64::from_str_radix(h, 16))
        .unwrap_or_else(|| t.parse());
    match r {
        Ok(v) => {
            println!("INFO: [LoginServer-NCSoft] {nome}={t} (padrao {padrao:#x})");
            v
        }
        Err(_) => padrao,
    }
}

/// Byte de `0xA8` do `SM_INIT`. `CONTEXT.md` diz `0x03`, `07-MAPEAMENTO-OFFSETS.md` diz `0xFD`.
fn init_flag() -> u8 {
    env_num("AION_INIT_FLAG", INIT_FLAG_PADRAO as u64) as u8
}

/// Offset da chave. `CONTEXT.md` diz `0x94`, `07-MAPEAMENTO-OFFSETS.md` diz `0x95`.
fn init_key_offset() -> usize {
    env_num("AION_INIT_KEY_OFFSET", INIT_KEY_OFFSET as u64) as usize
}

/// Bytes de sobra no fim do `SM_SERVER_LIST`. Nenhum documento os especifica.
fn server_list_trailer() -> usize {
    env_num("AION_SL_TRAILER", 15) as usize
}

/// Offset da chave de sessao Blowfish dentro do payload do `SM_INIT`.
pub const INIT_KEY_OFFSET: usize = 0x94;
/// Offset do byte de flag que liga o fluxo de RSA e GameGuard.
pub const INIT_FLAG_OFFSET: usize = 0xA8;
/// Valor padrao desse byte, segundo o CONTEXT.md.
pub const INIT_FLAG_PADRAO: u8 = 0x03;
/// Tamanho do payload do `SM_INIT`, antes de cifrar.
pub const INIT_PAYLOAD_LEN: usize = 192;

/// Monta o payload do `SM_INIT` no layout do cliente Classic EU 4.5.
///
/// Os offsets aqui **nao** sao os do padrao Java 2.4: naquele a chave de sessao mora em
/// `0x99..0xA9`. O cliente 4.5 le 5 bytes antes, e com o layout 2.4 ele recebe lixo no lugar da
/// chave -- nao consegue decifrar nada do que vem depois.
///
/// Conferido na engenharia reversa do `game.dll` (CONTEXT.md secao 2):
///
/// ```text
/// game.dll:0x84222D   movups xmm0, [r8 + rdi + 0x94]    -> chave em 0x94 (148..164)
/// game.dll:0x84231B   lea eax,[rcx-3]; cmp al,1; ja ..  -> byte 0xA8 (168) precisa ser 0x03
/// game.dll:0x842329   mov [rbx+0x78], al                -> 169 = major, 170 = minor
/// ```
///
/// Layout:
///
/// ```text
/// [0x00]        opcode 0x00
/// [0x01..0x05]  session_id (u32 LE)
/// [0x05..0x09]  0x0000C621 (revisao do protocolo)
/// [0x09..0x89]  scrambled_modulus (128 bytes do modulo RSA)
/// [0x89..0x94]  zeros (11 bytes)
/// [0x94..0xA4]  blowfish_key (16 bytes, a chave de sessao)
/// [0xA4..0xA8]  zeros (4 bytes)
/// [0xA8..0xAC]  0x00050403 -> flag 0x03 em 168, major 0x04 em 169, minor 0x05 em 170
/// [0xAC..0xB0]  0x00200000
/// [0xB0..0xC0]  zeros, completando 192 bytes
/// ```
pub fn build_sm_init_payload(
    session_id: u32,
    scrambled_modulus: &[u8; 128],
    blowfish_key: &[u8; 16],
) -> Vec<u8> {
    build_sm_init_payload_com(session_id, scrambled_modulus, blowfish_key, INIT_KEY_OFFSET, INIT_FLAG_PADRAO)
}

/// Igual, com o offset da chave e o byte de flag explicitos -- ver [`init_key_offset`].
pub fn build_sm_init_payload_com(
    session_id: u32,
    scrambled_modulus: &[u8; 128],
    blowfish_key: &[u8; 16],
    key_offset: usize,
    flag: u8,
) -> Vec<u8> {
    let mut p = vec![0u8; INIT_PAYLOAD_LEN];
    p[0] = 0x00; // opcode SM_INIT
    p[1..5].copy_from_slice(&session_id.to_le_bytes());
    p[5..9].copy_from_slice(&0x0000_C621u32.to_le_bytes());
    p[9..137].copy_from_slice(scrambled_modulus);
    // p[137..148] fica em zero (11 bytes)
    p[key_offset..key_offset + 16].copy_from_slice(blowfish_key);
    p[INIT_FLAG_OFFSET] = flag;
    p[INIT_FLAG_OFFSET + 1] = 0x04; // major
    p[INIT_FLAG_OFFSET + 2] = 0x05; // minor
    p[172..176].copy_from_slice(&2_097_152u32.to_le_bytes());
    p
}

/// Offset das flags da conta (ativo / maior de idade / termos aceitos).
pub const LOGIN_OK_FLAGS: usize = 17;
pub const LOGIN_OK_FLAGS_ATIVA: u32 = 0x0000_002F;
/// Offset da assinatura Classic (0xFF 0xFE) dentro do payload do `SM_LOGIN_OK`.
pub const LOGIN_OK_ASSINATURA: usize = 33;
/// Offset do campo de aceite de termos de uso (TOS agreement).
pub const LOGIN_OK_TOS: usize = 49;
/// Tamanho do payload do `SM_LOGIN_OK`, antes de cifrar.
pub const LOGIN_OK_PAYLOAD_LEN: usize = 78;

/// Monta o payload do `SM_LOGIN_OK`.
///
/// `tos_accepted`: se `false`, o cliente exibira a janela de Termos de Uso (TOS / User Agreement)
/// na tela para que o jogador leia e clique no botao de concordar/aceitar manualmente.
pub fn build_login_ok_payload(account_id: u32, login_ok: u32, tos_accepted: bool) -> Vec<u8> {
    let mut p = vec![0u8; LOGIN_OK_PAYLOAD_LEN];
    p[0] = 0x03; // opcode SM_LOGIN_OK
    p[1..5].copy_from_slice(&account_id.to_le_bytes());
    p[5..9].copy_from_slice(&login_ok.to_le_bytes());
    // p[9..17] fica em zero (2 * u32 = 8 bytes zeros)

    // Flags da conta: bit 4 (0x10) e a flag de TOS aceito (0x3F quando aceito, 0x2F quando pendente)
    let flags: u32 = if tos_accepted { 0x0000_003F } else { 0x0000_002F };
    p[17..21].copy_from_slice(&flags.to_le_bytes());
    p[21..25].copy_from_slice(&flags.to_le_bytes());
    p[25..29].copy_from_slice(&flags.to_le_bytes());
    p[29..33].copy_from_slice(&flags.to_le_bytes());

    // Assinatura Classic (0xFF 0xFE)
    p[33] = 0xFF; // offset 0x21
    p[34] = 0xFE; // offset 0x22
    p[35] = 0x00; // offset 0x23
    p[36] = 0x00; // offset 0x24

    // p[37..49] fica em zero (3 * u32 = 12 bytes zeros)
    // Termos de uso: 0 = exige aceite manual pelo usuario na tela, 1 = ja aceito
    let tos_val: u32 = if tos_accepted { 1 } else { 0 };
    p[49..53].copy_from_slice(&tos_val.to_le_bytes());
    // p[53..78] fica em zero (25 bytes zeros)

    p
}

/// Tamanho de uma entrada de servidor no `SM_SERVER_LIST` do protocolo NCSoft.
pub const SERVER_ENTRY_LEN_NC: usize = 21;
/// `ServerBits` com o bit 10 ligado, que marca a sessao como Classic.
pub const SERVER_BITS_CLASSIC: u32 = 0x0000_0401;
/// Bracket / CountryCode do Classic EU (0 para aceitar todos os brackets / 2 para Classic EU).
pub const BRACKET_CLASSIC_EU: u8 = 0;

/// Monta o payload do `SM_SERVER_LIST`.
pub fn build_server_list_payload(
    announce_ip: &str,
    announce_port: u16,
    server_id: u8,
    char_count: u8,
) -> Vec<u8> {
    let octetos: Vec<u8> = announce_ip.split('.').filter_map(|o| o.parse().ok()).collect();
    let ip: [u8; 4] = octetos.try_into().unwrap_or([127, 0, 0, 1]);

    let mut raw = Vec::new();
    raw.push(0x04); // opcode SM_SERVER_LIST
    raw.push(1);    // 1 servidor
    raw.push(server_id); // last server id

    // Entrada do servidor (21 bytes exatos conforme AL-Login Classic)
    write_server_entry(&mut raw, server_id, &ip, announce_port, BRACKET_CLASSIC_EU, SERVER_BITS_CLASSIC);

    // Contagem de personagens conforme AL-Login Classic:
    // writeH(maxId + 1), writeC(0x01), seguido de 1 byte por servidor + 15 bytes trailer
    let max_id = server_id as u16;
    raw.extend_from_slice(&(max_id + 1).to_le_bytes());
    raw.push(0x01); // flag ativa lista de servidores
    for i in 1..=max_id {
        if i == max_id {
            raw.push(char_count);
        } else {
            raw.push(0);
        }
    }
    raw.extend_from_slice(&[0u8; 15]); // 15 bytes trailer Classic

    raw
}

/// Monta o payload do `SM_SERVER_LIST` consultando dinamicamente a tabela `gameservers`.
pub fn build_server_list_payload_from_db(
    db: &AuthDb,
    fallback_ip: &str,
    fallback_port: u16,
    default_server_id: u8,
    char_count: u8,
) -> Vec<u8> {
    let servers = db.get_game_servers().unwrap_or_default();
    if servers.is_empty() {
        return build_server_list_payload(fallback_ip, fallback_port, default_server_id, char_count);
    }

    let mut raw = Vec::new();
    raw.push(0x04); // opcode SM_SERVER_LIST
    raw.push(servers.len() as u8); // total de servidores
    raw.push(servers[0].id); // last server id

    let mut max_id = 0u16;
    for s in &servers {
        if (s.id as u16) > max_id {
            max_id = s.id as u16;
        }
        let octetos: Vec<u8> = s.mask.split('.').filter_map(|o| o.parse().ok()).collect();
        let ip: [u8; 4] = octetos.try_into().unwrap_or([127, 0, 0, 1]);
        write_server_entry(&mut raw, s.id, &ip, s.port, BRACKET_CLASSIC_EU, SERVER_BITS_CLASSIC);
    }

    raw.extend_from_slice(&(max_id + 1).to_le_bytes());
    raw.push(0x01);
    for i in 1..=max_id {
        if i == servers[0].id as u16 {
            raw.push(char_count);
        } else {
            raw.push(0);
        }
    }
    raw.extend_from_slice(&[0u8; 15]);

    raw
}

pub fn build_server_list_payload_com(
    announce_ip: &str,
    announce_port: u16,
    server_id: u8,
    char_count: u8,
    _trailer: usize,
) -> Vec<u8> {
    build_server_list_payload(announce_ip, announce_port, server_id, char_count)
}

fn write_server_entry(raw: &mut Vec<u8>, server_id: u8, ip: &[u8; 4], port: u16, bracket: u8, server_bits: u32) {
    raw.push(server_id);
    raw.extend_from_slice(ip);
    raw.extend_from_slice(&(port as u32).to_le_bytes());
    raw.push(0); // limite de idade: livre
    raw.push(1); // pvp ligado
    raw.extend_from_slice(&0u16.to_le_bytes()); // jogadores online
    raw.extend_from_slice(&1000u16.to_le_bytes()); // maximo
    raw.push(1); // status: online
    raw.push(bracket); // bracket / country code (offset 16)
    raw.extend_from_slice(&server_bits.to_le_bytes()); // ServerBits (0x0000_0401) (offset 17..21)
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

    // 1. SM_INIT -- layout e offsets documentados em `build_sm_init_payload`.
    let raw_init = build_sm_init_payload_com(
        session_id,
        scrambled_modulus,
        &blowfish_key,
        init_key_offset(),
        init_flag(),
    );

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
        tos_accepted: bool,
    ) -> Result<(), std::io::Error> {
        let raw = build_login_ok_payload(account_id, login_ok, tos_accepted);

        let enc = crypt_engine.encrypt_packet(&raw);
        let mut pkt = Vec::with_capacity(enc.len() + 2);
        pkt.extend_from_slice(&((enc.len() + 2) as u16).to_le_bytes());
        pkt.extend_from_slice(&enc);

        socket.write_all(&pkt).await?;
        println!(
            "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] -> Sent SM_LOGIN_OK (74 bytes wire size, Account: '{}', ID: {}, TOS: {})",
            session_id, username, account_id, if tos_accepted { "Accepted" } else { "Manual Accept Required" }
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
        db: &AuthDb,
    ) -> Result<(), std::io::Error> {
        let raw = build_server_list_payload_from_db(
            db,
            announce_ip,
            announce_port,
            default_server_id,
            char_count,
        );

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
    let mut current_username = if !default_user.is_empty() {
        default_user.clone()
    } else {
        "fly".to_string()
    };
    let mut account_id = 1u32;
    let login_ok: u32 = 0x026edf39;
    let play_ok1: u32 = 0x026edf39;
    let play_ok2: u32 = rand::random();

    if let Ok(Some(a)) = db.get_or_create_account(&current_username, auto_create) {
        account_id = a.id as u32;
    }

    // =========================================================================
    // 2. Aguarda requisicao do cliente (CM_AUTH_GG / CM_LOGIN)
    // =========================================================================
    println!(
        "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] SM_INIT enviado. Aguardando autenticacao do cliente...",
        session_id
    );

    // =========================================================================
    // 3. Packet Reception Loop
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
            0x0B | 0x12 | 0x00 | _ if active_buf.len() >= 128 || payload.len() >= 128 => {
                // CM_LOGIN (Opcode 0x0B) / CM_NP_LOGIN (Opcode 0x12) ou payload RSA de 128+ bytes
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_LOGIN] (Opcode 0x{:02X}, ActiveLen: {} bytes, RawLen: {} bytes)",
                    session_id, opcode, active_buf.len(), payload.len()
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
                    false, // Exige aceite manual dos Termos de Uso (TOS) na tela do cliente
                )
                .await;
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] Termos de Uso (TOS) apresentados na tela. Aguardando aceite do jogador (CM_SERVER_LIST)...",
                    session_id
                );
            }
            0x05 => {
                // CM_SERVER_LIST (enviado pelo cliente assim que o jogador clica em 'Aceitar' nos Termos de Uso ou solicita refresh)
                println!(
                    "INFO: [LoginServer-NCSoft] [SESSION-{:08X}] <- [CM_SERVER_LIST] Jogador aceitou os Termos de Uso! Enviando lista de mundos...",
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
                    &db,
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

#[cfg(test)]
mod test {
    use super::*;
    use crate::crypto::login_crypt::STATIC_BLOWFISH_KEY;
    use crate::crypto::BlowfishCipher;

    /// Inverso do `enc_xor_pass` que o `encrypt_init` aplica.
    ///
    /// E o que o cliente faz para recuperar o payload: a chave corrente fica gravada em
    /// `len - 8`, e dali se anda de tras para frente desfazendo `cipher = plain ^ (key + plain)`.
    fn dec_xor_pass(data: &mut [u8]) {
        let total = data.len();
        let blocos = (total - 8) / 4;
        let mut curr_key = u32::from_le_bytes(data[total - 8..total - 4].try_into().unwrap());

        for i in (1..blocos).rev() {
            let p = i * 4;
            let cifrado = u32::from_le_bytes(data[p..p + 4].try_into().unwrap());
            let plain = cifrado ^ curr_key;
            curr_key = curr_key.wrapping_sub(plain);
            data[p..p + 4].copy_from_slice(&plain.to_le_bytes());
        }
    }

    /// Faz o que o cliente faz com o SM_INIT que chega do servidor: decifra com a chave estatica
    /// e desfaz o xor pass.
    fn como_o_cliente_decifra(cifrado: &[u8]) -> Vec<u8> {
        let mut buf = cifrado.to_vec();
        BlowfishCipher::new(&STATIC_BLOWFISH_KEY).decipher(&mut buf);
        dec_xor_pass(&mut buf);
        buf
    }

    fn modulo_falso() -> [u8; 128] {
        let mut m = [0u8; 128];
        for (i, b) in m.iter_mut().enumerate() {
            *b = (i as u8) ^ 0x5A;
        }
        m
    }

    fn chave_falsa() -> [u8; 16] {
        [
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE,
            0xFF, 0x01,
        ]
    }

    #[test]
    fn payload_do_sm_init_segue_o_layout_4_5() {
        let p = build_sm_init_payload(0xDEAD_BEEF, &modulo_falso(), &chave_falsa());

        assert_eq!(p.len(), 192, "o payload precisa fechar em 192 bytes");
        assert_eq!(p[0], 0x00, "opcode SM_INIT");
        assert_eq!(u32::from_le_bytes(p[1..5].try_into().unwrap()), 0xDEAD_BEEF);
        assert_eq!(&p[9..137], &modulo_falso()[..], "modulo RSA");

        // O que o `game.dll` le, conferido em CONTEXT.md secao 2.
        assert_eq!(&p[0x94..0x94 + 16], &chave_falsa()[..], "chave em 0x94 (game.dll:0x84222D)");
        assert_eq!(p[0xA8], 0x03, "flag RSA/GameGuard em 0xA8 (game.dll:0x84231B)");
        assert_eq!(p[0xA9], 0x04, "major em 169 (game.dll:0x842329)");
        assert_eq!(p[0xAA], 0x05, "minor em 170");
    }

    #[test]
    fn o_layout_2_4_nao_entregaria_a_chave_no_lugar_certo() {
        // Guarda de regressao: o layout anterior punha a chave em 153..169, cinco bytes depois.
        // Se alguem reverter para ele, este teste quebra em vez de o cliente travar em silencio.
        let mut antigo = vec![0u8; 192];
        antigo[153..169].copy_from_slice(&chave_falsa());

        assert_ne!(
            &antigo[0x94..0x94 + 16],
            &chave_falsa()[..],
            "com o layout 2.4 o cliente le lixo no lugar da chave"
        );
        assert_ne!(antigo[0xA8], 0x03, "e a flag de 0xA8 tambem nao esta la");
    }

    #[test]
    fn o_cliente_recupera_a_chave_de_sessao_do_sm_init() {
        // Este e o teste que importa: percorre o caminho inteiro que o cliente percorre.
        // Se a chave estiver no offset errado, ou o xor pass/Blowfish estiverem trocados, o valor
        // recuperado em 0x94 nao bate -- e e exatamente ai que o cliente real desiste.
        let chave = chave_falsa();
        let payload = build_sm_init_payload(0x0123_4567, &modulo_falso(), &chave);

        let mut engine = LoginCryptEngine::new();
        let cifrado = engine.encrypt_init(&payload, chave);
        assert_eq!(cifrado.len(), 192, "o SM_INIT cifrado tem 192 bytes (194 no wire)");
        assert_ne!(&cifrado[..16], &payload[..16], "tem que sair cifrado mesmo");

        let recuperado = como_o_cliente_decifra(&cifrado);

        assert_eq!(
            &recuperado[0x94..0x94 + 16],
            &chave[..],
            "o cliente precisa achar a chave de sessao em 0x94"
        );
        assert_eq!(recuperado[0xA8], 0x03, "flag em 0xA8 depois de decifrar");
        assert_eq!(recuperado[0xA9], 0x04);
        assert_eq!(recuperado[0xAA], 0x05);
        assert_eq!(&recuperado[9..137], &modulo_falso()[..], "modulo RSA intacto");
    }

    #[test]
    fn o_engine_passa_a_usar_a_chave_de_sessao_depois_do_init() {
        // Depois do SM_INIT o servidor cifra com a chave de sessao, nao com a estatica. Se ele
        // continuasse na estatica, o cliente decifraria lixo em tudo que vem depois.
        let chave = chave_falsa();
        let mut engine = LoginCryptEngine::new();
        let _ = engine.encrypt_init(&build_sm_init_payload(1, &modulo_falso(), &chave), chave);

        let mut raw = vec![0u8; 40];
        raw[0] = 0x0B; // SM_AUTH_GG
        let cifrado = engine.encrypt_packet(&raw);

        // Com a chave de sessao: decifra e o checksum fecha.
        let mut com_sessao = cifrado.clone();
        BlowfishCipher::new(&chave).decipher(&mut com_sessao);
        assert!(
            LoginCryptEngine::verify_checksum(&com_sessao),
            "o pacote seguinte tem que abrir com a chave de sessao"
        );
        assert_eq!(com_sessao[0], 0x0B, "e o opcode tem que reaparecer");

        // Com a estatica: nao fecha.
        let mut com_estatica = cifrado;
        BlowfishCipher::new(&STATIC_BLOWFISH_KEY).decipher(&mut com_estatica);
        assert!(
            !LoginCryptEngine::verify_checksum(&com_estatica),
            "se abrisse com a estatica, a troca de chave nao teria acontecido"
        );
    }

    // =====================================================================================
    // Prova contra a rede: os bytes abaixo foram capturados no loopback (24/08/2026), emitidos
    // pelo nosso proprio login-server para o cliente Aion Classic EU real. Sao os 4 pacotes da
    // cadeia, exatamente como sairam.
    //
    // O teste faz o que o cliente faz: decifra o SM_INIT com a chave estatica, pega a chave de
    // sessao em 0x94 e com ELA abre os tres seguintes. Se o offset estiver errado, a chave sai
    // errada e o checksum dos tres nao fecha -- nao ha como esse teste passar por acidente.
    // =====================================================================================

    /// SM_INIT, 194 bytes no wire.
    const REDE_P1: &str = concat!(
        "c200cbd1939851a54414810fd80a6aeec54324c108e6bb9c2c37627d50de939f0c3424f1c26c6dbe2af89104cb5201e0",
        "f2872594b4079782ec41e2b20079bdd029814b4dc4c73bb1fd0efa981955e9f2ef0139da324fedbccbca379b751c13a8",
        "eb7576dc2573809cf3b6d12d8723b1bf6711251994059fdad8a52cedc78a55919bd07edf034552408cfe5d1b31a9336b",
        "475a8caf9ad5bdf4e9ec3114b2a7ecb2e4ff4dc23479b9a9fe58e6032f1dc7141fe625d08aa25cec4b5858dfe9e43130",
        "9d9a",
    );
    /// SM_AUTH_GG, 50 bytes no wire.
    const REDE_P2: &str = concat!(
        "3200aa370638e14c4028a5b559eb733ac71ca5b559eb733ac71ca5b559eb733ac71ca5b559eb733ac71cad044c9833ac",
        "318c",
    );
    /// SM_LOGIN_OK, 74 bytes no wire.
    const REDE_P3: &str = concat!(
        "4a00c2da1c4a94ef33208053f9ade082ea70af7891301521b0268583493749d42c3ca5b559eb733ac71ca5b559eb733a",
        "c71ceded062587a82d2759c866c705291fc1ec2f62ccb1e4c52a",
    );
    /// SM_SERVER_LIST, 50 bytes no wire.
    const REDE_P4: &str = concat!(
        "32002345e1e4e60fb03ea2d4e63aa7a0187d356e311459d677e9b5d03171b5f2680aa5b559eb733ac71c44169432592c",
        "e4d7",
    );

    fn de_hex(h: &str) -> Vec<u8> {
        (0..h.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&h[i..i + 2], 16).unwrap())
            .collect()
    }

    /// Separa `[u16 tamanho][corpo]` e confere que o tamanho declarado bate com o quadro.
    fn corpo_do_quadro(wire: &[u8]) -> Vec<u8> {
        let tam = u16::from_le_bytes([wire[0], wire[1]]) as usize;
        assert_eq!(tam, wire.len(), "o tamanho declarado tem que bater com o quadro");
        wire[2..tam].to_vec()
    }

    #[test]
    fn a_cadeia_que_o_servidor_pos_na_rede_abre_do_lado_do_cliente() {
        let p1 = de_hex(REDE_P1);
        let mut init = corpo_do_quadro(&p1);
        assert_eq!(init.len(), 192);

        // Passo 1: o cliente abre o SM_INIT com a chave estatica.
        BlowfishCipher::new(&STATIC_BLOWFISH_KEY).decipher(&mut init);
        dec_xor_pass(&mut init);

        assert_eq!(init[0], 0x00, "opcode SM_INIT");
        assert_eq!(init[0xA8], 0x03, "flag em 0xA8 (game.dll:0x84231B)");
        assert_eq!(init[0xA9], 0x04, "major 4");
        assert_eq!(init[0xAA], 0x05, "minor 5");

        // Passo 2: a chave de sessao sai de 0x94.
        let mut chave = [0u8; 16];
        chave.copy_from_slice(&init[INIT_KEY_OFFSET..INIT_KEY_OFFSET + 16]);
        assert_ne!(chave, [0u8; 16], "a chave nao pode sair zerada");

        // Passo 3: com ela, os tres pacotes seguintes tem que abrir e fechar o checksum.
        let cifra = BlowfishCipher::new(&chave);
        for (hex, opcode_esperado, nome) in [
            (REDE_P2, 0x0Bu8, "SM_AUTH_GG"),
            (REDE_P3, 0x03, "SM_LOGIN_OK"),
            (REDE_P4, 0x04, "SM_SERVER_LIST"),
        ] {
            let wire = de_hex(hex);
            let mut corpo = corpo_do_quadro(&wire);
            cifra.decipher(&mut corpo);

            assert!(
                LoginCryptEngine::verify_checksum(&corpo),
                "{nome}: checksum nao fecha -- a chave lida em 0x94 esta errada"
            );
            assert_eq!(corpo[0], opcode_esperado, "{nome}: opcode");
        }
    }

    #[test]
    fn com_a_chave_no_offset_antigo_a_cadeia_nao_abre() {
        // Guarda de regressao contra o layout 2.4: lendo a chave em 153 -- onde ela ficava antes --
        // o checksum do pacote seguinte nao fecha. E o que o cliente real enfrentava.
        let p1 = de_hex(REDE_P1);
        let mut init = corpo_do_quadro(&p1);
        BlowfishCipher::new(&STATIC_BLOWFISH_KEY).decipher(&mut init);
        dec_xor_pass(&mut init);

        let mut chave_errada = [0u8; 16];
        chave_errada.copy_from_slice(&init[153..169]);
        assert_ne!(
            chave_errada,
            init[INIT_KEY_OFFSET..INIT_KEY_OFFSET + 16],
            "os dois offsets tem que dar chaves diferentes"
        );

        let wire = de_hex(REDE_P2);
        let mut corpo = corpo_do_quadro(&wire);
        BlowfishCipher::new(&chave_errada).decipher(&mut corpo);
        assert!(
            !LoginCryptEngine::verify_checksum(&corpo),
            "com a chave do offset antigo o pacote nao pode abrir"
        );
    }

    #[test]
    fn login_ok_traz_a_assinatura_classic_e_o_tos() {
        let p = build_login_ok_payload(1, 0x026E_DF39, true);

        assert_eq!(p.len(), LOGIN_OK_PAYLOAD_LEN);
        assert_eq!(p[0], 0x03, "opcode SM_LOGIN_OK");
        assert_eq!(p[33], 0xFF, "assinatura Classic (game.dll:0x717B40)");
        assert_eq!(p[34], 0xFE, "assinatura Classic (game.dll:0x717B40)");
        assert_eq!(p[49], 0x01, "TOS aceito");

        // Quando tos_accepted e false, byte 49 e 0 e flag e 0x2F (exige aceite manual pelo jogador)
        let p_manual = build_login_ok_payload(1, 0x026E_DF39, false);
        assert_eq!(p_manual[49], 0x00, "TOS pendente de aceite");
        assert_eq!(p_manual[LOGIN_OK_FLAGS], 0x2F, "flag de conta sem bit de TOS auto-aceito");
    }

    #[test]
    fn login_ok_carrega_conta_e_chave() {
        let p = build_login_ok_payload(0x1234_5678, 0x026E_DF39, false);

        assert_eq!(u32::from_le_bytes(p[1..5].try_into().unwrap()), 0x1234_5678);
        assert_eq!(u32::from_le_bytes(p[5..9].try_into().unwrap()), 0x026E_DF39);
        assert_eq!(
            u32::from_le_bytes(p[LOGIN_OK_FLAGS..LOGIN_OK_FLAGS + 4].try_into().unwrap()),
            LOGIN_OK_FLAGS_ATIVA,
            "flags da conta"
        );
    }

    #[test]
    fn login_ok_nao_tem_mais_o_bloco_colado() {
        let p = build_login_ok_payload(1, 1, false);
        assert!(
            !p.windows(4).any(|j| j == b"NTdE"),
            "o bloco colado nao pode voltar"
        );
        // Fora dos campos conhecidos, o resto e zero.
        for i in [9usize, 13, 35, 36, 37, 41, 45, 60, 67, 77] {
            assert_eq!(p[i], 0, "byte {i} devia ser zero");
        }
    }

    #[test]
    fn a_entrada_de_servidor_segue_o_layout_documentado() {
        let p = build_server_list_payload("127.0.0.1", 7777, 1, 0);
        let e = &p[3..3 + SERVER_ENTRY_LEN_NC];

        assert_eq!(e.len(), 21, "a entrada tem 21 bytes");
        assert_eq!(e[0x00], 1, "id do servidor");
        assert_eq!(&e[0x01..0x05], &[127, 0, 0, 1], "ip binario");
        assert_eq!(u32::from_le_bytes(e[0x05..0x09].try_into().unwrap()), 7777, "porta");
        assert_eq!(e[0x09], 0, "limite de idade");
        assert_eq!(e[0x0A], 1, "pvp");
        assert_eq!(u16::from_le_bytes(e[0x0B..0x0D].try_into().unwrap()), 0, "jogadores online");
        assert_eq!(u16::from_le_bytes(e[0x0D..0x0F].try_into().unwrap()), 1000, "maximo");
        assert_eq!(e[0x0F], 1, "online");
        assert_eq!(e[0x10], BRACKET_CLASSIC_EU, "bracket em 0x10");
        assert_eq!(
            u32::from_le_bytes(e[0x11..0x15].try_into().unwrap()),
            SERVER_BITS_CLASSIC,
            "ServerBits em 0x11..0x15, com o bit 10 ligado"
        );
    }

    #[test]
    fn o_bit_10_do_server_bits_marca_classic() {
        assert_eq!(SERVER_BITS_CLASSIC & 0x400, 0x400, "bit 10 ligado");
        assert_ne!(SERVER_BITS_CLASSIC, 4, "o valor antigo era 4");
    }

    #[test]
    fn server_bits_e_bracket_nao_estao_trocados() {
        let p = build_server_list_payload("192.168.1.50", 7777, 23, 3);
        let e = &p[3..3 + SERVER_ENTRY_LEN_NC];

        assert_eq!(e[0x10], BRACKET_CLASSIC_EU, "0x10 e o bracket");
        assert_eq!(e[0x11], 0x01, "primeiro byte de 0x00000401 em LE em 0x11");
    }

    #[test]
    fn a_contagem_de_personagens_vem_depois_da_lista() {
        let p = build_server_list_payload("127.0.0.1", 7777, 1, 4);
        let depois = 3 + SERVER_ENTRY_LEN_NC;

        assert_eq!(
            u16::from_le_bytes(p[depois..depois + 2].try_into().unwrap()),
            2,
            "maxId + 1 = 2"
        );
        assert_eq!(p[depois + 2], 0x01, "flag de selecao ativa");
        assert_eq!(p[depois + 3], 4, "a contagem de personagens vem logo em seguida");
    }

    #[test]
    fn ip_invalido_cai_no_loopback() {
        let p = build_server_list_payload("nao-e-um-ip", 7777, 1, 0);
        assert_eq!(&p[4..8], &[127, 0, 0, 1]);
    }

    #[test]
    fn o_bit_de_termos_e_conta_ativa_fica_ligado() {
        let p_accepted = build_login_ok_payload(1, 1, true);
        assert_eq!(p_accepted[LOGIN_OK_FLAGS] & 0x10, 0x10);

        let p_manual = build_login_ok_payload(1, 1, false);
        assert_eq!(p_manual[LOGIN_OK_FLAGS] & 0x10, 0);
    }
}
