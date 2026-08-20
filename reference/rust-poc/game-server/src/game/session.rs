use super::{message::client as c, ClientUpdate};

pub struct AuthServer {
    pub id: u32,
    pub key: u32,
}

pub struct Account {
    client_id: u16,
    character_id: u32,
    pin_enabled: bool,
    pub auth_server: AuthServer,
    /// Token the client presented in HqLogin — used to look up the username
    /// that STS associated with this session.
    pub session_token: String,
}

impl Account {
    pub fn new(client_id: u16) -> Self {
        Self {
            pin_enabled: false,
            client_id,
            character_id: 0,
            auth_server: AuthServer { id: 0, key: 0 },
            session_token: String::new(),
        }
    }

    pub fn send(&self, message: c::Message) -> ClientUpdate {
        ClientUpdate::new_with_token(
            self.client_id,
            self.character_id,
            message,
            self.session_token.clone(),
            self.auth_server.id,
        )
    }

    pub fn pin_enabled(&self) -> bool {
        self.pin_enabled
    }

    pub fn set_character_id(&mut self, character_id: u32) {
        self.character_id = character_id
    }
}
