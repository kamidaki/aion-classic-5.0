//! Efeitos de Dano Direto Físico e Mágico (DamageEffect / SpellAttackEffect - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::engine::damage::{CombatEngine, Hit, Type};
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::effect_model::Effect;

/// Efeito de Dano Físico Direto
#[derive(Debug, Clone)]
pub struct DamageEffect {
    pub base_damage: i32,
    pub skill_multiplier: f32,
    pub bonus_accuracy: i32,
    pub bonus_crit: i32,
}

impl DamageEffect {
    pub fn new(base_damage: i32, skill_multiplier: f32, bonus_accuracy: i32, bonus_crit: i32) -> Self {
        Self {
            base_damage,
            skill_multiplier,
            bonus_accuracy,
            bonus_crit,
        }
    }

    /// Calcula o golpe físico contra um monstro/NPC
    pub fn calculate_hit_on_npc(&self, caster: &Character, _target: &Entity) -> Hit {
        let atk = (caster.stats.secondary.main_hand_attack as i32 + self.base_damage).max(1) as u16;
        let acc = (caster.stats.secondary.main_hand_accuracy as i32 + self.bonus_accuracy).max(1) as u16;
        let crit = (caster.stats.secondary.main_hand_crit as i32 + self.bonus_crit).max(0) as u16;

        CombatEngine::calculate_physical_hit(
            atk,
            self.skill_multiplier,
            100, // Defesa física padrão
            acc,
            100, // Evasion alvo
            100, // Block alvo
            100, // Parry alvo
            crit,
            50,  // Resist crit alvo
            1.5, // Multiplicador crítico
        )
    }
}

impl EffectTrait for DamageEffect {
    fn apply_to_entity(&self, effect: &mut Effect, target: &mut Entity) {
        let damage = (self.base_damage.max(1) as f32 * self.skill_multiplier) as i32;
        target.hp.update(-damage);
        effect.value = damage;
    }

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        let damage = (self.base_damage.max(1) as f32 * self.skill_multiplier) as i32;
        target.stats.hp.update(-damage);
        effect.value = damage;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}

/// Efeito de Dano Mágico Direto (SpellAttackEffect)
#[derive(Debug, Clone)]
pub struct SpellAttackEffect {
    pub base_spell_damage: i32,
    pub element: crate::skillengine::model::skill_type::SkillElement,
}

impl SpellAttackEffect {
    pub fn new(base_spell_damage: i32, element: crate::skillengine::model::skill_type::SkillElement) -> Self {
        Self {
            base_spell_damage,
            element,
        }
    }

    pub fn calculate_magic_damage(&self, magic_boost: i32, magic_resist: i32) -> i32 {
        let boost_factor = 1.0 + (magic_boost as f32 / 1000.0);
        let resist_factor = (1.0 - (magic_resist as f32 / 10000.0)).clamp(0.0, 1.0);
        ((self.base_spell_damage as f32 * boost_factor) * resist_factor).max(1.0) as i32
    }
}

impl EffectTrait for SpellAttackEffect {
    fn apply_to_entity(&self, effect: &mut Effect, target: &mut Entity) {
        let dmg = self.base_spell_damage.max(1);
        target.hp.update(-dmg);
        effect.value = dmg;
    }

    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character) {
        let dmg = self.base_spell_damage.max(1);
        target.stats.hp.update(-dmg);
        effect.value = dmg;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
