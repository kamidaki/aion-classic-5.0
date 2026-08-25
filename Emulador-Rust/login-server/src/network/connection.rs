//! Estado de uma conexão de login no protocolo NCSoft.
//!
//! Espelha os estados do `LoginSession` do Java AionEmu:
//! `CONNECTED` → `AUTHED_GG` → `AUTHED_LOGIN`

/// Estado atual de uma sessão de login (protocolo NCSoft).
#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum ConnectionState {
    /// Conexão estabelecida; `SM_INIT` enviado, aguardando `CM_AUTH_GG`.
    Connected,
    /// `CM_AUTH_GG` recebido; `SM_AUTH_GG` enviado, aguardando `CM_LOGIN`.
    AuthedGg,
    /// `CM_LOGIN` recebido e validado; `SM_LOGIN_OK` enviado,
    /// aguardando `CM_SERVER_LIST` e depois `CM_PLAY`.
    AuthedLogin,
}

/// Contexto completo de uma sessão de login em progresso.
pub struct LoginSession {
    pub session_id: u32,
    pub state: ConnectionState,
    /// Nome de usuário autenticado (preenchido após `CM_LOGIN`).
    pub username: String,
    /// ID da conta no banco (preenchido após `CM_LOGIN`).
    pub account_id: u32,
    /// Token de sessão `login_ok` enviado ao game-server.
    pub login_ok: u32,
    /// Token `play_ok1` gerado aleatoriamente.
    pub play_ok1: u32,
    /// Token `play_ok2` gerado aleatoriamente.
    pub play_ok2: u32,
}

impl LoginSession {
    pub fn new(session_id: u32) -> Self {
        Self {
            session_id,
            state: ConnectionState::Connected,
            username: String::new(),
            account_id: 0,
            login_ok: 0x026edf39,
            play_ok1: 0x026edf39,
            play_ok2: rand::random(),
        }
    }
}
