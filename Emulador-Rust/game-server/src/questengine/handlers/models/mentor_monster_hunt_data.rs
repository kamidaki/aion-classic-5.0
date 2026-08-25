//! Dados para Missões de Caça de Mentor com Aprendiz (MentorMonsterHuntData - Padrão Java Aion Classic 2.8 / 4.5)

use super::monster::Monster;

#[derive(Debug, Clone)]
pub struct MentorMonsterHuntData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub monsters: Vec<Monster>,
    pub min_mentor_level_diff: u8,
}

impl MentorMonsterHuntData {
    pub fn new(start_npc_id: u32, end_npc_id: u32, min_mentor_level_diff: u8) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            monsters: Vec::new(),
            min_mentor_level_diff,
        }
    }

    pub fn with_monster(mut self, monster: Monster) -> Self {
        self.monsters.push(monster);
        self
    }
}
