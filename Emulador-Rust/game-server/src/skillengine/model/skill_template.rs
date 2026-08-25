//! Template Estático de Habilidade (SkillTemplate - Padrão Java Aion Classic 2.8 / 4.5)

use crate::skillengine::model::skill_target_slot::SkillTargetSlot;
use crate::skillengine::model::skill_type::{SkillElement, SkillSubType, SkillType};

#[derive(Debug, Clone)]
pub struct SkillTemplate {
    pub skill_id: u32,
    pub name: String,
    pub skill_type: SkillType,
    pub sub_type: SkillSubType,
    pub target_slot: SkillTargetSlot,
    pub element: SkillElement,
    pub cast_time_ms: u32,
    pub cooldown_ms: u32,
    pub range: f32,
    pub radius: f32,
    pub hp_cost: u32,
    pub mp_cost: u32,
    pub dp_cost: u32,
    pub required_level: u8,
    pub is_enemy_target: bool,
    pub is_charge_skill: bool,
    pub max_charge_stages: u8,
    pub cancel_rate: f32,
}

impl SkillTemplate {
    pub fn new(
        skill_id: u32,
        name: impl Into<String>,
        skill_type: SkillType,
        sub_type: SkillSubType,
        cast_time_ms: u32,
        cooldown_ms: u32,
        range: f32,
        mp_cost: u32,
    ) -> Self {
        Self {
            skill_id,
            name: name.into(),
            skill_type,
            sub_type,
            target_slot: match sub_type {
                SkillSubType::Buff => SkillTargetSlot::Buff,
                SkillSubType::Debuff => SkillTargetSlot::Debuff,
                _ => SkillTargetSlot::None,
            },
            element: SkillElement::None,
            cast_time_ms,
            cooldown_ms,
            range,
            radius: 0.0,
            hp_cost: 0,
            mp_cost,
            dp_cost: 0,
            required_level: 1,
            is_enemy_target: sub_type == SkillSubType::Attack || sub_type == SkillSubType::Debuff,
            is_charge_skill: false,
            max_charge_stages: 0,
            cancel_rate: 0.5,
        }
    }
}
