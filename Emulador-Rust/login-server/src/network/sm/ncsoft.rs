//! Pacotes Server → Client do protocolo NCSoft (porta 2106).
//!
//! Builders de cada pacote enviado ao cliente.
//! Os offsets e layouts foram verificados por engenharia reversa do `game.dll` (client 4.5 EU Classic).

// Re-exporta os builders do módulo legado para compatibilidade
pub use crate::net::ncsoft::{
    build_sm_init_payload,
    build_sm_init_payload_com,
    build_login_ok_payload,
    build_server_list_payload,
    build_server_list_payload_from_db,
    build_server_list_payload_com,
    // Constantes de opcode / layout
    INIT_KEY_OFFSET,
    INIT_FLAG_OFFSET,
    INIT_FLAG_PADRAO,
    INIT_PAYLOAD_LEN,
    LOGIN_OK_FLAGS,
    LOGIN_OK_FLAGS_ATIVA,
    LOGIN_OK_ASSINATURA,
    LOGIN_OK_TOS,
    LOGIN_OK_PAYLOAD_LEN,
    SERVER_ENTRY_LEN_NC,
    SERVER_BITS_CLASSIC,
    BRACKET_CLASSIC_EU,
};

// ─── Opcodes Server → Client ────────────────────────────────────────────────

/// Opcode do `SM_INIT` — primeiro pacote enviado ao cliente na conexão.
pub const SM_INIT: u8 = 0x00;
/// Opcode do `SM_AUTH_GG` — resposta ao CM_AUTH_GG do GameGuard.
pub const SM_AUTH_GG: u8 = 0x0B;
/// Opcode do `SM_LOGIN_OK` — autenticação aceita.
pub const SM_LOGIN_OK: u8 = 0x03;
/// Opcode do `SM_SERVER_LIST` — lista de servidores de jogo.
pub const SM_SERVER_LIST: u8 = 0x04;
/// Opcode do `SM_PLAY_OK` — autorização para entrar no servidor escolhido.
pub const SM_PLAY_OK: u8 = 0x07;
/// Opcode do `SM_LOGIN_FAIL` — falha de autenticação.
pub const SM_LOGIN_FAIL: u8 = 0x01;

// ─── Opcodes Client → Server ─────────────────────────────────────────────────

/// Opcode do `CM_AUTH_GG` — cliente responde ao SM_INIT.
pub const CM_AUTH_GG: u8 = 0x07;
/// Opcode do `CM_LOGIN` — cliente envia credenciais RSA.
pub const CM_LOGIN: u8 = 0x0B;
/// Opcode do `CM_SERVER_LIST` — cliente solicita lista de servidores.
pub const CM_SERVER_LIST: u8 = 0x05;
/// Opcode do `CM_PLAY` — cliente escolheu um servidor.
pub const CM_PLAY: u8 = 0x02;
