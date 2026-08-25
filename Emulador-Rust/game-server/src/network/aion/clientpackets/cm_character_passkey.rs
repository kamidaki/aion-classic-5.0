//! Pacote CM_CHARACTER_PASSKEY

#[derive(Debug, Clone)]
pub struct CmCharacterPasskey {
    pub passkey: String,
    pub action_type: u8,
}
