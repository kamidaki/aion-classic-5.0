//! Container de Efeitos Ativos na Criatura (EffectsContainer - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct ActiveEffect {
    pub skill_id: u32,
    pub effect_id: u32,
    pub duration_seconds: u32,
    pub is_debuff: bool,
    pub stat_modifiers: HashMap<String, i32>,
}

impl ActiveEffect {
    pub fn new(skill_id: u32, effect_id: u32, duration_seconds: u32, is_debuff: bool) -> Self {
        Self {
            skill_id,
            effect_id,
            duration_seconds,
            is_debuff,
            stat_modifiers: HashMap::new(),
        }
    }

    pub fn with_modifier(mut self, stat: &str, value: i32) -> Self {
        self.stat_modifiers.insert(stat.to_string(), value);
        self
    }
}

#[derive(Debug, Clone, Default)]
pub struct EffectsContainer {
    pub effects: HashMap<u32, ActiveEffect>, // (skill_id, ActiveEffect)
}

impl EffectsContainer {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_effect(&mut self, effect: ActiveEffect) {
        self.effects.insert(effect.skill_id, effect);
    }

    pub fn remove_effect(&mut self, skill_id: u32) -> Option<ActiveEffect> {
        self.effects.remove(&skill_id)
    }

    pub fn has_effect(&self, skill_id: u32) -> bool {
        self.effects.contains_key(&skill_id)
    }

    pub fn count_buffs(&self) -> usize {
        self.effects.values().filter(|e| !e.is_debuff).count()
    }

    pub fn count_debuffs(&self) -> usize {
        self.effects.values().filter(|e| e.is_debuff).count()
    }

    pub fn clear(&mut self) {
        self.effects.clear();
    }
}
