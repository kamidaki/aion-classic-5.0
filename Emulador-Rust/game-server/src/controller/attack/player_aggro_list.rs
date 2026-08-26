//! Lista de Ameaça de Jogador (PlayerAggroList - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;

#[derive(Debug, Clone, Default)]
pub struct PlayerAggroList {
    pub attacking_monsters: HashSet<u32>,
}

impl PlayerAggroList {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_attacker(&mut self, npc_id: u32) {
        self.attacking_monsters.insert(npc_id);
    }

    pub fn remove_attacker(&mut self, npc_id: u32) {
        self.attacking_monsters.remove(&npc_id);
    }

    pub fn is_in_combat(&self) -> bool {
        !self.attacking_monsters.is_empty()
    }

    pub fn clear(&mut self) {
        self.attacking_monsters.clear();
    }
}
