//! Pacote CM_DUEL_REQUEST

#[derive(Debug, Clone)]
pub struct CmDuelRequest {
    pub target_player_id: u32,
    pub duel_type: u8,
}
