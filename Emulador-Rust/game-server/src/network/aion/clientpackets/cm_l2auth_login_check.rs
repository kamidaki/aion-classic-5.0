//! Pacote CM_L2AUTH_LOGIN_CHECK (Opcode 0x00E4 / 0x00E7)

#[derive(Debug, Clone)]
pub struct CmL2AuthLoginCheck {
    pub account_id: u32,
    pub session_key: [u8; 8],
}
