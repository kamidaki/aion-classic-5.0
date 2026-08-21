use super::{message::client as c, ClientUpdate};

pub struct AuthServer {
    pub id: u32,
    pub key: u32,
}

pub struct Account {
    client_id: u16,
    character_id: u32,
    pin_enabled: bool,
    /// Verdadeiro depois do C_LEVEL_READY. Dali em diante quase nada esta implementado, e o replay
    /// passa a servir tambem os opcodes que tem handler -- ver `ClientMessages::deserialise`.
    no_mundo: bool,
    pub auth_server: AuthServer,
    /// Token the client presented in HqLogin — used to look up the username
    /// that STS associated with this session.
    pub session_token: String,
}

impl Account {
    pub fn new(client_id: u16) -> Self {
        Self {
            pin_enabled: false,
            no_mundo: false,
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

    pub fn character_id(&self) -> u32 {
        self.character_id
    }

    pub fn no_mundo(&self) -> bool {
        self.no_mundo
    }

    pub fn entrou_no_mundo(&mut self) {
        self.no_mundo = true;
    }
}
