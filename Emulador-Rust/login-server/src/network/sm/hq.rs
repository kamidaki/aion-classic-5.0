//! Pacotes Server → Client do protocolo Gameforge HQ (porta 13001).
//!
//! Builders de cada pacote enviado ao cliente HQ.
//! Enquadramento: `[u16 tamanho][u8 opcode][3 bytes zero][payload]`
//!
//! Re-exporta as funções públicas do módulo de implementação (`net::hq`).

// Re-exporta as funções de build do módulo legado
pub use crate::net::hq::{
    parse_credentials,
    build_login_ok,
    build_server_list,
    build_play_ok,
    Credentials,
};

// ─── Opcodes HQ Server → Client ──────────────────────────────────────────────

/// Opcode HQ `AUTH_GREETING` (0x05) — primeiro pacote enviado ao cliente HQ.
pub const HQ_AUTH_GREETING: u8 = 0x05;
/// Opcode HQ `LOGIN_OK` (0x01) — autenticação aceita.
pub const HQ_LOGIN_OK: u8 = 0x01;
/// Opcode HQ `SERVER_LIST` (0x02) — lista de servidores.
pub const HQ_SERVER_LIST: u8 = 0x02;
/// Opcode HQ `PLAY_OK` (0x04) — autorização para entrar no servidor.
pub const HQ_PLAY_OK: u8 = 0x04;

// ─── Opcodes HQ Client → Server ──────────────────────────────────────────────

/// Opcode HQ `CM_CREDENTIALS` (0x01) — cliente envia credenciais base64.
pub const CM_HQ_CREDENTIALS: u8 = 0x01;
/// Opcode HQ `CM_SELECT_SERVER` (0x02) — cliente escolheu um servidor.
pub const CM_HQ_SELECT_SERVER: u8 = 0x02;
