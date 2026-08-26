//! Pacote SM_BATTLEPASS_LIST

#[derive(Debug, Clone)]
pub struct SmBattlepassList {
    pub current_season: u32,
    pub player_points: u32,
    pub current_level: u32,
    pub is_unlocked_premium: bool,
}
