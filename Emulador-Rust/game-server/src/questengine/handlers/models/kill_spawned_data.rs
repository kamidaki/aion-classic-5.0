//! Dados para Missões de Matar Inimigo Invocado (KillSpawnedData - Padrão Java Aion Classic 2.8 / 4.5)

use super::spawned_monster::SpawnedMonster;

#[derive(Debug, Clone)]
pub struct KillSpawnedData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub spawned_monsters: Vec<SpawnedMonster>,
}

impl KillSpawnedData {
    pub fn new(start_npc_id: u32, end_npc_id: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            spawned_monsters: Vec::new(),
        }
    }

    pub fn with_spawned_monster(mut self, monster: SpawnedMonster) -> Self {
        self.spawned_monsters.push(monster);
        self
    }
}
