//! Pacotes do Servidor para Instâncias e Masmorras (SM_INSTANCE_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct SmInstantDungeonInfo {
    pub instance_id: u32,
    pub map_id: u32,
    pub stage: u8,
    pub remaining_time_seconds: u32,
    pub score: i32,
}

#[derive(Debug, Clone)]
pub struct SmInstanceDungeonCooltimes {
    pub player_id: u32,
    pub cooldowns: Vec<(u32, u32)>, // (world_id, remaining_seconds)
}
