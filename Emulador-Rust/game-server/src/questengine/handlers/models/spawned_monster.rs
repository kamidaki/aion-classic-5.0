//! Dados de Monstro Spawnado por Ação de Missão (SpawnedMonster - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct SpawnedMonster {
    pub npc_id: u32,
    pub spawn_time: u32,
}

impl SpawnedMonster {
    pub fn new(npc_id: u32, spawn_time: u32) -> Self {
        Self {
            npc_id,
            spawn_time,
        }
    }
}
