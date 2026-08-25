//! Estado de uma conexão de chat.

/// Estado da sessão de um cliente de chat.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChatConnectionState {
    /// Conexão estabelecida; aguardando `CM_CHAT_INIT`.
    Connected,
    /// `CM_CHAT_INIT` recebido; aguardando `CM_PLAYER_AUTH`.
    Initialized,
    /// `CM_PLAYER_AUTH` validado; cliente pode enviar/receber mensagens.
    Authenticated,
}
