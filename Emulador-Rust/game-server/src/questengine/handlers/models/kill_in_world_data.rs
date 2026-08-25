//! Dados para Missões de Eliminação por Mapa / Mundo (KillInWorldData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct KillInWorldData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub world_id: u32,
    pub target_count: u32,
}

impl KillInWorldData {
    pub fn new(start_npc_id: u32, end_npc_id: u32, world_id: u32, target_count: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            world_id,
            target_count,
        }
    }
}
