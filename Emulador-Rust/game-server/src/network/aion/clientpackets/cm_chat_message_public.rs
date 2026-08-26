//! Pacote CM_CHAT_MESSAGE_PUBLIC

#[derive(Debug, Clone)]
pub struct CmChatMessagePublic {
    pub chat_type: u8,
    pub message: String,
}
