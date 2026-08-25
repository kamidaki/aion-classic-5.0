//! Efeitos de Melhoria de Atributos (StatupEffect / BuffEffect - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Efeito de Buff de Atributo Físico ou Mágico
#[derive(Debug, Clone)]
pub struct BuffEffect {
    pub attack_boost: i32,
    pub defense_boost: i32,
    pub magic_boost: i32,
    pub speed_boost_percent: f32,
    pub duration_ms: u32,
}

impl EffectTrait for BuffEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.duration_ms = self.duration_ms;

        // Aplica modificadores nos atributos secundários
        target.stats.secondary.main_hand_attack = (target.stats.secondary.main_hand_attack as i32 + self.attack_boost).max(0) as u16;
        target.stats.secondary.magic_boost = (target.stats.secondary.magic_boost as i32 + self.magic_boost).max(0) as u16;
        if self.speed_boost_percent > 0.0 {
            target.stats.move_speed *= 1.0 + (self.speed_boost_percent / 100.0);
        }
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}

    fn end_on_player(&self, _effect: &Effect, target: &mut Character) {
        target.stats.secondary.main_hand_attack = (target.stats.secondary.main_hand_attack as i32 - self.attack_boost).max(0) as u16;
        target.stats.secondary.magic_boost = (target.stats.secondary.magic_boost as i32 - self.magic_boost).max(0) as u16;
        if self.speed_boost_percent > 0.0 {
            target.stats.move_speed /= 1.0 + (self.speed_boost_percent / 100.0);
        }
    }
}
