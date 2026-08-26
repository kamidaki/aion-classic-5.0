//! Controlador de Efeitos e Estados Anormais de Criaturas (EffectController - Padrão Java Aion Classic 2.8 / 4.5)

use super::effects_container::{ActiveEffect, EffectsContainer};

#[derive(Debug, Clone, Default)]
pub struct EffectController {
    pub container: EffectsContainer,
    pub abnormal_state: u32,
}

impl EffectController {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_effect(&mut self, effect: ActiveEffect) {
        self.container.add_effect(effect);
    }

    pub fn remove_effect(&mut self, skill_id: u32) -> Option<ActiveEffect> {
        self.container.remove_effect(skill_id)
    }

    pub fn has_effect(&self, skill_id: u32) -> bool {
        self.container.has_effect(skill_id)
    }

    pub fn dispel_debuffs(&mut self, count: usize) {
        let debuff_keys: Vec<u32> = self
            .container
            .effects
            .iter()
            .filter(|(_, eff)| eff.is_debuff)
            .take(count)
            .map(|(k, _)| *k)
            .collect();

        for key in debuff_keys {
            self.container.remove_effect(key);
        }
    }

    pub fn set_abnormal_state(&mut self, state_bit: u32) {
        self.abnormal_state |= state_bit;
    }

    pub fn unset_abnormal_state(&mut self, state_bit: u32) {
        self.abnormal_state &= !state_bit;
    }

    pub fn has_abnormal_state(&self, state_bit: u32) -> bool {
        (self.abnormal_state & state_bit) != 0
    }
}
