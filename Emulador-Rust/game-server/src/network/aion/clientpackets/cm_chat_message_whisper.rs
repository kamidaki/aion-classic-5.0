//! Pacote CM_CHAT_MESSAGE_WHISPER

#[derive(Debug, Clone)]
pub struct CmChatMessageWhisper {
    pub recipient_name: String,
    pub message: String,
}
