//! Efeito de Furtividade / Invisibilidade (HideEffect - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Nível de Furtividade (Hide I, II, III)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HideLevel {
    Basic,    // Nível 1 (detectado por Search I)
    Advanced, // Nível 2 (detectado por Search II)
    Master,   // Nível 3 (Shadow Walk)
}

/// Efeito de Invisibilidade (HideEffect - Assassin / Ranger)
#[derive(Debug, Clone)]
pub struct HideEffect {
    pub hide_level: HideLevel,
    pub speed_penalty_percent: f32,
    pub duration_ms: u32,
}

impl EffectTrait for HideEffect {
    fn apply_to_entity(&self, _effect: &mut Effect, _target: &mut Entity) {}

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::HIDE;
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.duration_ms = self.duration_ms;

        if self.speed_penalty_percent > 0.0 {
            target.stats.move_speed *= 1.0 - (self.speed_penalty_percent / 100.0);
        }
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}

    fn end_on_player(&self, _effect: &Effect, target: &mut Character) {
        if self.speed_penalty_percent > 0.0 {
            target.stats.move_speed /= 1.0 - (self.speed_penalty_percent / 100.0);
        }
    }
}
