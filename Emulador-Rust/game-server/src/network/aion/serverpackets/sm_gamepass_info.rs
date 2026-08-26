//! Pacote SM_GAMEPASS_INFO

#[derive(Debug, Clone)]
pub struct SmGamepassInfo {
    pub active_pass_id: u32,
    pub expiration_timestamp: u64,
}
