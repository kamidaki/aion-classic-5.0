//! Opcode constants for all Login Server protocols.

// ─── NCSoft 2106 Protocol Opcodes (Server → Client) ──────────────────────────

/// Opcode do `SM_INIT` (0x00) — inicialização de conexão e envio de chave RSA/Blowfish.
pub const SM_INIT: u8 = 0x00;
/// Opcode do `SM_AUTH_GG` (0x0B) — resposta ao CM_AUTH_GG do GameGuard.
pub const SM_AUTH_GG: u8 = 0x0B;
/// Opcode do `SM_LOGIN_OK` (0x03) — autenticação aceita com sucesso.
pub const SM_LOGIN_OK: u8 = 0x03;
/// Opcode do `SM_SERVER_LIST` (0x04) — lista de servidores de jogo ativos.
pub const SM_SERVER_LIST: u8 = 0x04;
/// Opcode do `SM_PLAY_OK` (0x07) — token de autorização para entrar no GameServer.
pub const SM_PLAY_OK: u8 = 0x07;
/// Opcode do `SM_LOGIN_FAIL` (0x01) — falha de autenticação (usuário/senha inválidos, banido).
pub const SM_LOGIN_FAIL: u8 = 0x01;

// ─── NCSoft 2106 Protocol Opcodes (Client → Server) ──────────────────────────

/// Opcode do `CM_AUTH_GG` (0x07) — cliente responde ao SM_INIT.
pub const CM_AUTH_GG: u8 = 0x07;
/// Opcode do `CM_LOGIN` (0x0B) — cliente envia credenciais RSA.
pub const CM_LOGIN: u8 = 0x0B;
/// Opcode do `CM_SERVER_LIST` (0x05) — cliente solicita lista de servidores.
pub const CM_SERVER_LIST: u8 = 0x05;
/// Opcode do `CM_PLAY` (0x02) — cliente escolheu um servidor.
pub const CM_PLAY: u8 = 0x02;

// ─── Gameforge HQ 13001 Protocol Opcodes ─────────────────────────────────────

/// Opcode HQ `AUTH_GREETING` (0x05) — saudação inicial HQ.
pub const HQ_AUTH_GREETING: u8 = 0x05;
/// Opcode HQ `LOGIN_OK` (0x01) — login aceito no HQ.
pub const HQ_LOGIN_OK: u8 = 0x01;
/// Opcode HQ `SERVER_LIST` (0x02) — lista de servidores HQ.
pub const HQ_SERVER_LIST: u8 = 0x02;
/// Opcode HQ `PLAY_OK` (0x04) — autorização para entrar no servidor HQ.
pub const HQ_PLAY_OK: u8 = 0x04;
/// Opcode HQ `CM_CREDENTIALS` (0x01) — envio de credenciais HQ.
pub const CM_HQ_CREDENTIALS: u8 = 0x01;
/// Opcode HQ `CM_SELECT_SERVER` (0x02) — seleção de servidor HQ.
pub const CM_HQ_SELECT_SERVER: u8 = 0x02;

// ─── Inter-Server GS 9014 Protocol Opcodes ───────────────────────────────────

/// Opcode `SM_GS_AUTH` (0x01) — GameServer autentica com LoginServer.
pub const CM_GS_AUTH: u8 = 0x01;
/// Opcode `SM_GS_AUTH_RESPONSE` (0x01) — LoginServer responde à autenticação.
pub const SM_GS_AUTH_RESPONSE: u8 = 0x01;
/// Opcode `CM_GS_ACCOUNT_RECONNECT` (0x02) — GameServer consulta sessão de reconexão.
pub const CM_GS_ACCOUNT_RECONNECT: u8 = 0x02;
/// Opcode `SM_GS_ACCOUNT_RECONNECT_RESPONSE` (0x02) — LoginServer confirma sessão.
pub const SM_GS_ACCOUNT_RECONNECT_RESPONSE: u8 = 0x02;
