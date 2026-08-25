//! Pacote SM_MESSAGE

#[derive(Debug, Clone)]
pub struct SmMessage {
    pub sender_name: String,
    pub message: String,
    pub chat_type: u8,
}
