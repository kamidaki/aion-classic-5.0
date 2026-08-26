//! Efeitos de Cura e Regeneração (Heal, MP Heal, DP Heal - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Cura Instantânea de HP (HealInstantEffect)
#[derive(Debug, Clone)]
pub struct HealInstantEffect {
    pub heal_amount: i32,
}

impl EffectTrait for HealInstantEffect {
    fn apply_to_entity(&self, effect: &mut Effect, target: &mut Entity) {
        target.hp.update(self.heal_amount);
        effect.value = self.heal_amount;
    }

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        target.stats.hp.update(self.heal_amount);
        effect.value = self.heal_amount;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Cura Contínua / Regeneração de HP (HealOverTimeEffect - HoT)
#[derive(Debug, Clone)]
pub struct HealOverTimeEffect {
    pub tick_heal: i32,
    pub interval_ms: u32,
    pub duration_ms: u32,
}

impl EffectTrait for HealOverTimeEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_heal;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.tick_interval_ms = self.interval_ms;
        effect.duration_ms = self.duration_ms;
        effect.value = self.tick_heal;
    }

    fn on_tick_entity(&self, effect: &Effect, target: &mut Entity) {
        target.hp.update(effect.value);
    }

    fn on_tick_player(&self, effect: &Effect, target: &mut Character) {
        target.stats.hp.update(effect.value);
    }

    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Restauração Instantânea de MP (MpHealInstantEffect)
#[derive(Debug, Clone)]
pub struct MpHealInstantEffect {
    pub mp_amount: i32,
}

impl EffectTrait for MpHealInstantEffect {
    fn apply_to_entity(&self, _effect: &mut Effect, _target: &mut Entity) {}

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        target.stats.mp.update(self.mp_amount);
        effect.value = self.mp_amount;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Restauração Instantânea de DP (DpHealInstantEffect)
#[derive(Debug, Clone)]
pub struct DpHealInstantEffect {
    pub dp_amount: u32,
}

impl EffectTrait for DpHealInstantEffect {
    fn apply_to_entity(&self, _effect: &mut Effect, _target: &mut Entity) {}

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        target.stats.dp.update(self.dp_amount as i32);
        effect.value = self.dp_amount as i32;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
