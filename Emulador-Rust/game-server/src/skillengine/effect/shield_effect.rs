//! Efeitos de Escudo e Absorção de Dano (ShieldEffect / MpShieldEffect - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

/// Efeito de Escudo de Absorção de Dano (ShieldEffect - Sorcerer Stone Skin / Cleric Shield)
#[derive(Debug, Clone)]
pub struct ShieldEffect {
    pub max_capacity: i32,
    pub duration_ms: u32,
}

impl EffectTrait for ShieldEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = AbnormalStateMask::SHIELD;
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.shield_capacity = self.max_capacity;
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = AbnormalStateMask::SHIELD;
        effect.target_slot = SkillTargetSlot::Buff;
        effect.dispel_category = DispelCategoryType::Buff;
        effect.shield_capacity = self.max_capacity;
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

impl ShieldEffect {
    /// Absorve dano recebido. Retorna o dano restante não absorvido.
    pub fn absorb_damage(effect: &mut Effect, incoming_damage: i32) -> i32 {
        if effect.shield_capacity <= 0 {
            return incoming_damage;
        }

        if incoming_damage <= effect.shield_capacity {
            effect.shield_capacity -= incoming_damage;
            0 // Todo o dano foi mitigado pelo escudo
        } else {
            let overflow = incoming_damage - effect.shield_capacity;
            effect.shield_capacity = 0;
            effect.is_active = false; // Escudo quebrou
            overflow
        }
    }
}
