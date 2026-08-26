//! Registro e Histórico de Mortes (KillList - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;

#[derive(Debug, Clone, Default)]
pub struct KillList {
    pub kills: HashMap<u32, u32>, // (victim_id, count)
}

impl KillList {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn record_kill(&mut self, victim_id: u32) {
        *self.kills.entry(victim_id).or_insert(0) += 1;
    }

    pub fn get_kill_count(&self, victim_id: u32) -> u32 {
        self.kills.get(&victim_id).copied().unwrap_or(0)
    }

    pub fn total_kills(&self) -> u32 {
        self.kills.values().sum()
    }
}
