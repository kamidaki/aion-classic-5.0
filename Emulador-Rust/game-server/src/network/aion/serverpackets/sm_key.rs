//! Pacote SM_KEY (Opcode 0x0113 / 0x00D9)

#[derive(Debug, Clone)]
pub struct SmKey {
    pub session_key: [u8; 8],
}
