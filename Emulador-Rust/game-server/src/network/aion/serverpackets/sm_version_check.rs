//! Pacote SM_VERSION_CHECK (Opcode 0x00E4)

#[derive(Debug, Clone)]
pub struct SmVersionCheck {
    pub version: u32,
    pub server_mode: u8,
}
