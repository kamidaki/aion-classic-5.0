//! Estatísticas de Criaturas e Jogadores (CreatureStats / PlayerStats - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::model::stats::stat_enum::StatEnum;
use crate::model::stats::stat_modifiers::{StatModifier, StatModifierType};

#[derive(Debug, Clone, Default)]
pub struct CreatureStats {
    pub base_stats: HashMap<StatEnum, i32>,
    pub modifiers: Vec<StatModifier>,
}

impl CreatureStats {
    pub fn new() -> Self {
        Self {
            base_stats: HashMap::new(),
            modifiers: Vec::new(),
        }
    }

    pub fn set_base_stat(&mut self, stat: StatEnum, value: i32) {
        self.base_stats.insert(stat, value);
    }

    pub fn get_base_stat(&self, stat: StatEnum) -> i32 {
        self.base_stats.get(&stat).copied().unwrap_or(0)
    }

    pub fn add_modifier(&mut self, modifier: StatModifier) {
        self.modifiers.push(modifier);
    }

    pub fn remove_modifiers_by_source(&mut self, source_id: u32) {
        self.modifiers.retain(|m| m.source_id != source_id);
    }

    pub fn get_effective_stat(&self, stat: StatEnum) -> i32 {
        let base = self.get_base_stat(stat);
        let mut add = 0;
        let mut percent = 0;

        for m in &self.modifiers {
            if m.stat == stat {
                match m.modifier_type {
                    StatModifierType::Add => add += m.value,
                    StatModifierType::Percent => percent += m.value,
                }
            }
        }

        let total_add = base + add;
        if percent != 0 {
            (total_add as f32 * (1.0 + (percent as f32 / 100.0))) as i32
        } else {
            total_add
        }
    }
}
