//! Pacotes do Servidor para Loja e Passe Daeva (SM_BATTLEPASS_* / SM_GAMEPASS_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct SmBattlepassList {
    pub current_season: u32,
    pub player_points: u32,
    pub current_level: u32,
    pub is_unlocked_premium: bool,
}

#[derive(Debug, Clone)]
pub struct SmGamepassInfo {
    pub active_pass_id: u32,
    pub expiration_timestamp: u64,
}
