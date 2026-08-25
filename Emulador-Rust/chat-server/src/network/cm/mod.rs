//! Pacotes Client → Server do Chat Server.
//!
//! Re-exporta as variantes do enum [`crate::protocol::ChatClientPacket`]
//! e define os opcodes.

// Re-exporta do módulo de implementação legado
pub use crate::protocol::ChatClientPacket;

// ─── Opcodes Client → Server ──────────────────────────────────────────────────

/// Opcode `CM_CHAT_INIT` (0x01) — cliente inicia conexão com versão do protocolo.
pub const CM_CHAT_INIT: u8 = 0x01;
/// Opcode `CM_PLAYER_AUTH` (0x02) — cliente autentica com player_id e token.
pub const CM_PLAYER_AUTH: u8 = 0x02;
/// Opcode `CM_CHANNEL_JOIN` (0x03) — cliente entra num canal.
pub const CM_CHANNEL_JOIN: u8 = 0x03;
/// Opcode `CM_CHANNEL_LEAVE` (0x04) — cliente sai de um canal.
pub const CM_CHANNEL_LEAVE: u8 = 0x04;
/// Opcode `CM_CHANNEL_MESSAGE` (0x05) — cliente envia mensagem num canal.
pub const CM_CHANNEL_MESSAGE: u8 = 0x05;
/// Opcode `CM_PING` (0x06) — keepalive do cliente.
pub const CM_PING: u8 = 0x06;
