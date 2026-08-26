//! Conexão de Sessão do Jogador (AionConnection - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;
use crate::network::packet_flood_filter::PacketFloodFilter;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ConnectionState {
    #[default]
    Connected,
    Authed,
    InGame,
    Closed,
}

#[derive(Debug, Clone)]
pub struct AionConnection {
    pub session_id: u32,
    pub account_id: Option<u32>,
    pub player_id: Option<u32>,
    pub state: ConnectionState,
    pub session_key: [u8; 8],
    pub mac_address: Option<String>,
    pub last_ping: Instant,
    pub flood_filter: PacketFloodFilter,
}

impl AionConnection {
    pub fn new(session_id: u32) -> Self {
        Self {
            session_id,
            account_id: None,
            player_id: None,
            state: ConnectionState::Connected,
            session_key: [0u8; 8],
            mac_address: None,
            last_ping: Instant::now(),
            flood_filter: PacketFloodFilter::default(),
        }
    }

    pub fn set_authed(&mut self, account_id: u32, session_key: [u8; 8]) {
        self.account_id = Some(account_id);
        self.session_key = session_key;
        self.state = ConnectionState::Authed;
    }

    pub fn set_in_game(&mut self, player_id: u32) {
        self.player_id = Some(player_id);
        self.state = ConnectionState::InGame;
    }

    pub fn is_in_game(&self) -> bool {
        self.state == ConnectionState::InGame
    }

    pub fn close(&mut self) {
        self.state = ConnectionState::Closed;
    }
}
