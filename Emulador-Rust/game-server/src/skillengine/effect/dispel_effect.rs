//! Efeitos de Dispel e Purificação (DispelBuff / DispelDebuff / Cleanse - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::DispelCategoryType;

/// Efeito de Remoção de Buffs ou Debuffs (Dispel / Cleanse / Purify)
#[derive(Debug, Clone)]
pub struct DispelEffect {
    pub dispel_category: DispelCategoryType,
    pub max_count: usize,
    pub max_power: u32,
}

impl DispelEffect {
    pub fn new(dispel_category: DispelCategoryType, max_count: usize, max_power: u32) -> Self {
        Self {
            dispel_category,
            max_count,
            max_power,
        }
    }

    /// Filtra e remove efeitos que batem com a categoria especificada
    pub fn process_dispel(&self, active_effects: &mut Vec<Effect>) -> Vec<u32> {
        let mut dispelled_skills = Vec::new();
        let mut count = 0;

        active_effects.retain(|eff| {
            if count >= self.max_count {
                return true;
            }

            let matches = match self.dispel_category {
                DispelCategoryType::All => true,
                DispelCategoryType::Buff => eff.dispel_category == DispelCategoryType::Buff,
                DispelCategoryType::Debuff => {
                    eff.dispel_category == DispelCategoryType::Debuff
                        || eff.dispel_category == DispelCategoryType::DebuffPhysical
                        || eff.dispel_category == DispelCategoryType::DebuffMental
                }
                DispelCategoryType::DebuffPhysical => {
                    eff.dispel_category == DispelCategoryType::DebuffPhysical
                }
                DispelCategoryType::DebuffMental => {
                    eff.dispel_category == DispelCategoryType::DebuffMental
                }
                _ => false,
            };

            if matches {
                dispelled_skills.push(eff.skill_id);
                count += 1;
                false // Remove da lista de efeitos ativos
            } else {
                true
            }
        });

        dispelled_skills
    }
}

impl EffectTrait for DispelEffect {
    fn apply_to_entity(&self, _effect: &mut Effect, _target: &mut Entity) {}
    fn apply_to_player(&self, _effect: &mut Effect, _target: &mut Character) {}
    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
