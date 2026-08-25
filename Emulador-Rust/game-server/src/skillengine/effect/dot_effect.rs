//! Efeitos de Dano Contínuo / DoT (Bleed, Poison, Curse, Disease - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Efeito de Sangramento (BleedEffect)
#[derive(Debug, Clone)]
pub struct BleedEffect {
    pub tick_damage: i32,
    pub interval_ms: u32,
    pub duration_ms: u32,
}

impl EffectTrait for BleedEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::BLEED;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::BLEED;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn on_tick_entity(&self, effect: &Effect, target: &mut Entity) {
        target.hp.update(-effect.value);
    }

    fn on_tick_player(&self, effect: &Effect, target: &mut Character) {
        target.stats.hp.update(-effect.value);
    }

    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Envenenamento (PoisonEffect)
#[derive(Debug, Clone)]
pub struct PoisonEffect {
    pub tick_damage: i32,
    pub interval_ms: u32,
    pub duration_ms: u32,
}

impl EffectTrait for PoisonEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::POISON;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::POISON;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffPhysical;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn on_tick_entity(&self, effect: &Effect, target: &mut Entity) {
        target.hp.update(-effect.value);
    }

    fn on_tick_player(&self, effect: &Effect, target: &mut Character) {
        target.stats.hp.update(-effect.value);
    }

    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Maldição (CurseEffect)
#[derive(Debug, Clone)]
pub struct CurseEffect {
    pub tick_damage: i32,
    pub interval_ms: u32,
    pub duration_ms: u32,
}

impl EffectTrait for CurseEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::CURSE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::CURSE;
        effect.target_slot = SkillTargetSlot::Debuff;
        effect.dispel_category = DispelCategoryType::DebuffMental;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_damage;
    }

    fn on_tick_entity(&self, effect: &Effect, target: &mut Entity) {
        target.hp.update(-effect.value);
    }

    fn on_tick_player(&self, effect: &Effect, target: &mut Character) {
        target.stats.hp.update(-effect.value);
    }

    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
