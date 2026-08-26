//! Pacote SM_INSTANCE_DUNGEON_COOLTIMES

#[derive(Debug, Clone)]
pub struct SmInstanceDungeonCooltimes {
    pub player_id: u32,
    pub cooldowns: Vec<(u32, u32)>,
}
