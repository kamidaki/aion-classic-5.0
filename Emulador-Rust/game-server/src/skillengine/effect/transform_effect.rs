//! Efeitos de Transformação e Polimorfia (TransformEffect / PolymorphEffect - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};
use crate::skillengine::model::transform_type::TransformType;

/// Efeito de Transformação (Avatar divino DP, Formas de Classe ou Árvore/Curse of Roots)
#[derive(Debug, Clone)]
pub struct TransformEffect {
    pub transform_type: TransformType,
    pub model_id: u32,
    pub duration_ms: u32,
}

impl EffectTrait for TransformEffect {
    fn apply_to_entity(&self, effect: &mut Effect, _target: &mut Entity) {
        effect.abnormal_state = match self.transform_type {
            TransformType::Avatar => AbnormalStateMask::TRANSFORM,
            TransformType::Polymorph => AbnormalStateMask::SHAPECHANGE | AbnormalStateMask::SILENCE,
            _ => AbnormalStateMask::TRANSFORM,
        };
        effect.target_slot = match self.transform_type {
            TransformType::Polymorph => SkillTargetSlot::Debuff,
            _ => SkillTargetSlot::Buff,
        };
        effect.dispel_category = match self.transform_type {
            TransformType::Polymorph => DispelCategoryType::DebuffMental,
            _ => DispelCategoryType::Buff,
        };
        effect.duration_ms = self.duration_ms;
    }

    fn apply_to_player(&self, effect: &mut Effect, _target: &mut Character) {
        effect.abnormal_state = match self.transform_type {
            TransformType::Avatar => AbnormalStateMask::TRANSFORM,
            TransformType::Polymorph => AbnormalStateMask::SHAPECHANGE | AbnormalStateMask::SILENCE,
            _ => AbnormalStateMask::TRANSFORM,
        };
        effect.target_slot = match self.transform_type {
            TransformType::Polymorph => SkillTargetSlot::Debuff,
            _ => SkillTargetSlot::Buff,
        };
        effect.dispel_category = match self.transform_type {
            TransformType::Polymorph => DispelCategoryType::DebuffMental,
            _ => DispelCategoryType::Buff,
        };
        effect.duration_ms = self.duration_ms;
    }

    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
