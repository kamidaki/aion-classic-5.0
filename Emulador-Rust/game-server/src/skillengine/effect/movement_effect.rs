//! Efeitos de Movimento Forçado e Queda (Knockback, Stumble, Pulled, OpenAerial - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Efeito de Empurrão para Trás (KnockbackEffect)
#[derive(Debug, Clone)]
pub struct KnockbackEffect {
    pub distance: f32,
}

impl EffectTrait for KnockbackEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::KNOCKBACK;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = 1000;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::KNOCKBACK;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = 1000;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Queda ao Chão (StumbleEffect)
#[derive(Debug, Clone)]
pub struct StumbleEffect {
    pub duration_ms: u32,
}

impl EffectTrait for StumbleEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::STUMBLE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::STUMBLE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Puxão em Direção ao Conjurador (PulledEffect - Templar Hook / Gladiator)
#[derive(Debug, Clone)]
pub struct PulledEffect;

impl EffectTrait for PulledEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::STUN;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = 1000;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::STUN;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = 1000;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Levitação no Ar (OpenAerialEffect - Sorcerer / Assassin)
#[derive(Debug, Clone)]
pub struct OpenAerialEffect {
    pub duration_ms: u32,
}

impl EffectTrait for OpenAerialEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::OPEN_AERIAL;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::OPEN_AERIAL;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::None;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
