//! Grupos de Jogadores (PlayerGroup - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;
use crate::model::team::loot_rules::{LootRuleType, LootThreshold};

#[derive(Debug, Clone)]
pub struct PlayerGroupModel {
    pub group_id: u32,
    pub leader_id: u32,
    pub members: HashSet<u32>,
    pub loot_rule: LootRuleType,
    pub loot_threshold: LootThreshold,
    pub max_members: usize,
}

impl PlayerGroupModel {
    pub fn new(group_id: u32, leader_id: u32) -> Self {
        let mut members = HashSet::new();
        members.insert(leader_id);

        Self {
            group_id,
            leader_id,
            members,
            loot_rule: LootRuleType::RoundRobin,
            loot_threshold: LootThreshold::Heroic,
            max_members: 6,
        }
    }

    pub fn add_member(&mut self, player_id: u32) -> Result<(), &'static str> {
        if self.members.len() >= self.max_members {
            return Err("Grupo cheio (máx 6 membros)");
        }
        self.members.insert(player_id);
        Ok(())
    }

    pub fn remove_member(&mut self, player_id: u32) -> bool {
        self.members.remove(&player_id)
    }
}
