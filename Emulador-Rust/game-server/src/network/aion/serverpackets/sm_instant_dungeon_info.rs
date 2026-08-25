//! Pacote SM_INSTANT_DUNGEON_INFO

#[derive(Debug, Clone)]
pub struct SmInstantDungeonInfo {
    pub instance_id: u32,
    pub map_id: u32,
    pub stage: u8,
    pub remaining_time_seconds: u32,
    pub score: i32,
}
