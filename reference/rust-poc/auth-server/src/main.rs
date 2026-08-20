mod error;

use std::io::{Read, Write};
use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::thread::spawn;

use error::Result;

fn main() {
    println!("INFO: Starting Auth Server");

    for port in [13001u16, 2106] {
        let listener = TcpListener::bind(format!("0.0.0.0:{port}")).unwrap();
        println!("INFO: Listening on {}", listener.local_addr().unwrap());
        spawn(move || {
            while let Ok((stream, _)) = listener.accept() {
                spawn(|| {
                    if let Err(e) = handle(stream) {
                        println!("ERROR: auth session failed: {e}");
                    }
                });
            }
        });
    }

    // Keep main thread alive
    loop {
        std::thread::sleep(std::time::Duration::from_secs(3600));
    }
}

// ---------------------------------------------------------------------------
// Protocol constants
// ---------------------------------------------------------------------------

/// Opcode 0x05 — Auth greeting sent immediately on connect.
/// Payload: auth_key_1 (null-terminated), auth_key_2 (null-terminated),
///          service name "aiongfc" (null-terminated), then 4 trailer bytes.
/// The two keys are opaque UUIDs used by the client for HMAC-style auth.
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

const ACCOUNT_ID: u32 = 0x0000_0015;
const LOGIN_OK_KEY: u32 = 0x0262_cab6;

/// Opcode 0x01 — Login OK, sent after receiving the client credential packet.
fn login_ok() -> [u8; 14] {
    let mut bytes = [0u8; 14];
    let len = bytes.len() as u16;
    bytes[0..2].copy_from_slice(&len.to_le_bytes());
    bytes[2] = 0x01;
    bytes[6..10].copy_from_slice(&ACCOUNT_ID.to_le_bytes());
    bytes[10..14].copy_from_slice(&LOGIN_OK_KEY.to_le_bytes());
    bytes
}

/// Opcode 0x04 — play OK, sent after the client picks a game server.
/// bytes[14..18] MUST be zero — the client interprets any non-zero value there
/// as an "Authorization Error" code and disconnects before reaching the game server.
fn session_key(server_selection: &[u8], server_id: u8) -> [u8; 22] {
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
    // bytes[14..18] = 0 (zeros = success; non-zero = AuthorizationError shown to client)
    bytes[20] = server_id;
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
    /// 0x4 = normal world server, 0x5 = instance server
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

        // IP as 4 binary bytes (network/big-endian order), port immediately after.
        // The client reads these as raw bytes, not as a null-terminated ASCII string.
        bytes[13..17].copy_from_slice(&self.ip_addr.octets());
        bytes[17..19].copy_from_slice(&self.port.to_be_bytes());

        if self.typ == 0x4 {
            bytes[19] = 0x1;
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

    /// Add a server to the list. Silently ignores the entry if the list is
    /// already at MAX capacity (20 servers).
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

        buf[0] = len as u8;
        buf[2] = Self::SEQUENCE_NUMBER;
        buf[6] = self.servers.len() as u8;

        len
    }
}

/// Build the default server list shown to every connecting client.
fn default_server_list() -> GameServerList {
    let game_ip = game_server_ip();
    let mut list = GameServerList::new(0x15);
    list.insert(GameServer {
        id: 0x15,
        ip_addr: game_ip,
        online: true,
        port: 7777,
        typ: 4,
        characters: 1,
    });
    list.insert(GameServer {
        id: 0x16,
        ip_addr: game_ip,
        online: true,
        port: 7777,
        typ: 4,
        characters: 0,
    });
    list.insert(GameServer {
        id: 0x67,
        ip_addr: game_ip,
        online: false,
        port: 7777,
        typ: 5,
        characters: 0,
    });
    list
}

fn selected_server_id(buf: &[u8]) -> u8 {
    if buf.len() > 6 && matches!(buf[6], 0x15 | 0x16 | 0x67) {
        return buf[6];
    }

    0x15
}

fn game_server_ip() -> Ipv4Addr {
    std::env::var("AION_GAME_IP")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or_else(|| Ipv4Addr::new(192, 168, 100, 77))
}

// ---------------------------------------------------------------------------
// Per-connection handler
// ---------------------------------------------------------------------------

fn handle(mut stream: TcpStream) -> Result<()> {
    let peer = stream.peer_addr()?;
    println!("INFO: incoming {peer}");

    // Shared read buffer reused for all client reads this session.
    let mut buf = [0u8; 512];

    // 1. Greet: send auth keys + service name
    stream.write_all(&AUTH_GREETING)?;
    println!("DEBUG: → AUTH_GREETING ({} bytes)", AUTH_GREETING.len());

    // 2. Receive client credentials (username / password hash — not yet verified)
    let len = stream.read(&mut buf)?;
    println!("DEBUG: ← credentials ({len} bytes): {:02X?}", &buf[..len]);

    // 3. Acknowledge login
    let login_ok = login_ok();
    stream.write_all(&login_ok)?;
    println!("DEBUG: → LOGIN_OK: {:02X?}", login_ok);

    // 4. Send game server list
    // Upper bound: MAX servers × 63 bytes + 8 preamble + 4 suffix = 1272 bytes.
    let mut gs_buf = [0u8; 2048];
    let gs_len = default_server_list().serialise(&mut gs_buf);
    stream.write_all(&gs_buf[..gs_len])?;
    println!(
        "INFO: server list summary: len={} msg_type={} count6={} count7={} first_online={} first_id={} first_ip={}.{}.{}.{} first_port={}",
        gs_len,
        gs_buf[2],
        gs_buf[6],
        gs_buf[7],
        gs_buf[12],
        gs_buf[13],
        gs_buf[21],
        gs_buf[22],
        gs_buf[23],
        gs_buf[24],
        u16::from_be_bytes([gs_buf[25], gs_buf[26]]),
    );
    println!("DEBUG: → server list ({gs_len} bytes): {:02X?}", &gs_buf[..gs_len]);

    // 5. Receive server selection from client
    let len = stream.read(&mut buf)?;
    if len == 0 {
        println!("WARN: client closed connection after server list (rejected list — error 6?)");
        return Ok(());
    }
    println!("DEBUG: ← server selection ({len} bytes): {:02X?}", &buf[..len]);
    let selected_server_id = selected_server_id(&buf[..len]);
    println!("INFO: selected server id: {selected_server_id} (default 0x15 when packet omits it)");

    // 6. Send session key → client forwards it to game server on connect
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
        let gs = GameServer {
            id: 0x15,
            ip_addr: Ipv4Addr::new(127, 0, 0, 1),
            online: true,
            port: 7777,
            typ: 4,
            characters: 1,
        };

        // Binary IP [13..17], port BE [17..19], world-flag [19], zeros [20..63]
        let target = [
            0x01, 0x04, 0x00, 0x00, 0x01, 0x15, 0x00, 0x00, 0x00, 0x01, 0x00,
            0x00, 0x00, 0x7F, 0x00, 0x00, 0x01, 0x1E, 0x61, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ];
        assert_eq!(gs.serialise(), target);
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
        assert_eq!(key[20], 0x15);
    }

    #[test]
    fn test_game_servers_list_single() {
        let mut gsl = GameServerList::new(0x15);
        gsl.insert(GameServer {
            id: 0x15,
            ip_addr: Ipv4Addr::new(127, 0, 0, 1),
            online: true,
            port: 7777,
            typ: 4,
            characters: 1,
        });

        let mut buf = [0u8; 2048];
        let len = gsl.serialise(&mut buf);

        let target = [
            75, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00,
            // server entry: header, binary IP, port, world-flag, padding
            0x01, 0x04, 0x00, 0x00, 0x01, 0x15, 0x00, 0x00, 0x00, 0x01, 0x00,
            0x00, 0x00, 0x7F, 0x00, 0x00, 0x01, 0x61, 0x1E, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            // suffix
            0x15, 0x00, 0x00, 0x00,
        ];
        assert_eq!(buf[..len], target);
    }

    #[test]
    fn test_game_servers_list_multi() {
        let mut gsl = GameServerList::new(0x15);
        gsl.insert(GameServer {
            id: 0x15,
            ip_addr: Ipv4Addr::new(127, 0, 0, 1),
            online: true,
            port: 7777,
            typ: 4,
            characters: 1,
        });
        gsl.insert(GameServer {
            id: 0x67,
            ip_addr: Ipv4Addr::new(127, 0, 0, 1),
            online: false,
            port: 7777,
            typ: 5,
            characters: 0,
        });

        let mut buf = [0u8; 2048];
        let len = gsl.serialise(&mut buf);

        let target: [u8; 138] = [
            138, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00,
            // server 0x15: world, online, binary IP, port 7777, world-flag=1
            0x01, 0x04, 0x00, 0x00, 0x01, 0x15, 0x00, 0x00, 0x00, 0x01, 0x00,
            0x00, 0x00, 0x7F, 0x00, 0x00, 0x01, 0x61, 0x1E, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            // server 0x67: instance, offline, binary IP, port 7777, world-flag=0
            0x01, 0x05, 0x00, 0x00, 0x00, 0x67, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x7F, 0x00, 0x00, 0x01, 0x61, 0x1E, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            // suffix
            0x15, 0x00, 0x00, 0x00,
        ];
        assert_eq!(buf[..len], target);
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
