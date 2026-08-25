//! Dados para Template de Caça a Monstros (MonsterHuntData - Padrão Java Aion Classic 2.8 / 4.5)

use super::monster::Monster;

#[derive(Debug, Clone)]
pub struct MonsterHuntData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub monsters: Vec<Monster>,
}

impl MonsterHuntData {
    pub fn new(start_npc_id: u32, end_npc_id: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            monsters: Vec::new(),
        }
    }

    pub fn with_monster(mut self, monster: Monster) -> Self {
        self.monsters.push(monster);
        self
    }
}
