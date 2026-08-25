//! Pacote SM_SYSTEM_MESSAGE (Opcode 0x00E3 / SM_MESSAGE_CODE)

#[derive(Debug, Clone)]
pub struct SmSystemMessage {
    pub message_id: u32,
    pub params: Vec<String>,
}
