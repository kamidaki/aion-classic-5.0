//! Pacotes Server → Client do Chat Server.
//!
//! Re-exporta os builders de [`crate::protocol::ChatServerPackets`]
//! e define os opcodes.

// Re-exporta os builders do módulo de implementação legado
pub use crate::protocol::ChatServerPackets;

// ─── Opcodes Server → Client ──────────────────────────────────────────────────

/// Opcode `SM_CHAT_INI` (0x01) — servidor confirma inicialização da sessão de chat.
pub const SM_CHAT_INI: u8 = 0x01;
/// Opcode `SM_PLAYER_AUTH` (0x02) — servidor confirma autenticação do jogador.
pub const SM_PLAYER_AUTH: u8 = 0x02;
/// Opcode `SM_CHANNEL_MESSAGE` (0x05) — servidor distribui mensagem de canal.
pub const SM_CHANNEL_MESSAGE: u8 = 0x05;
/// Opcode `SM_PONG` (0x06) — resposta ao CM_PING.
pub const SM_PONG: u8 = 0x06;
