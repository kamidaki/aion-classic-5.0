//! Pacote CM_VERSION_CHECK (Opcode 0x00E4)

#[derive(Debug, Clone)]
pub struct CmVersionCheck {
    pub version: u32,
}
