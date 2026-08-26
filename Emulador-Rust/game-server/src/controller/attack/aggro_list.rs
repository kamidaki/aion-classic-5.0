//! Tabela de Ameaça/Ódio de Criaturas (AggroList - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use super::aggro_info::AggroInfo;

#[derive(Debug, Clone, Default)]
pub struct AggroList {
    pub list: HashMap<u32, AggroInfo>,
}

impl AggroList {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_hate(&mut self, attacker_id: u32, hate: i32) {
        self.list
            .entry(attacker_id)
            .or_insert_with(|| AggroInfo::new(attacker_id))
            .add_hate(hate);
    }

    pub fn add_damage(&mut self, attacker_id: u32, damage: i32) {
        self.list
            .entry(attacker_id)
            .or_insert_with(|| AggroInfo::new(attacker_id))
            .add_damage(damage);
    }

    pub fn get_most_hated(&self) -> Option<u32> {
        self.list
            .values()
            .max_by_key(|info| info.hate)
            .map(|info| info.attacker_id)
    }

    pub fn remove(&mut self, attacker_id: u32) {
        self.list.remove(&attacker_id);
    }

    pub fn clear(&mut self) {
        self.list.clear();
    }

    pub fn is_empty(&self) -> bool {
        self.list.is_empty()
    }
}
