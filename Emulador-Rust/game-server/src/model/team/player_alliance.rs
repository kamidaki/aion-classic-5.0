//! Alianças de Grupos (PlayerAlliance - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;
use crate::model::team::loot_rules::{LootRuleType, LootThreshold};

#[derive(Debug, Clone)]
pub struct PlayerAllianceModel {
    pub alliance_id: u32,
    pub captain_id: u32,
    pub vice_captains: HashSet<u32>,
    pub members: HashSet<u32>,
    pub loot_rule: LootRuleType,
    pub loot_threshold: LootThreshold,
    pub max_members: usize,
}

impl PlayerAllianceModel {
    pub fn new(alliance_id: u32, captain_id: u32) -> Self {
        let mut members = HashSet::new();
        members.insert(captain_id);

        Self {
            alliance_id,
            captain_id,
            vice_captains: HashSet::new(),
            members,
            loot_rule: LootRuleType::Leader,
            loot_threshold: LootThreshold::Fabled,
            max_members: 24,
        }
    }
}
