//! Efeitos de Controle de Grupo / CC (Stun, Sleep, Root, Silence, Bind, Blind, Fear, Paralyze - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Efeito de Atordoamento (StunEffect)
#[derive(Debug, Clone)]
pub struct StunEffect {
    pub duration_ms: u32,
}

impl EffectTrait for StunEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::STUN;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::STUN;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Sono (SleepEffect)
#[derive(Debug, Clone)]
pub struct SleepEffect {
    pub duration_ms: u32,
}

impl EffectTrait for SleepEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::SLEEP;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::SLEEP;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Imobilização (RootEffect)
#[derive(Debug, Clone)]
pub struct RootEffect {
    pub duration_ms: u32,
}

impl EffectTrait for RootEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::ROOT;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::ROOT;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Silêncio Mágico (SilenceEffect)
#[derive(Debug, Clone)]
pub struct SilenceEffect {
    pub duration_ms: u32,
}

impl EffectTrait for SilenceEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::SILENCE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::SILENCE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Paralisia de Ataque Físico (BindEffect)
#[derive(Debug, Clone)]
pub struct BindEffect {
    pub duration_ms: u32,
}

impl EffectTrait for BindEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::BIND;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::BIND;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Cegueira / Redução Drástica de Precisão (BlindEffect)
#[derive(Debug, Clone)]
pub struct BlindEffect {
    pub duration_ms: u32,
}

impl EffectTrait for BlindEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::BLIND;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::BLIND;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Medo / Pânico (FearEffect)
#[derive(Debug, Clone)]
pub struct FearEffect {
    pub duration_ms: u32,
}

impl EffectTrait for FearEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::FEAR;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::FEAR;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Paralisia Total (ParalyzeEffect)
#[derive(Debug, Clone)]
pub struct ParalyzeEffect {
    pub duration_ms: u32,
}

impl EffectTrait for ParalyzeEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::PARALYZE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::PARALYZE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
