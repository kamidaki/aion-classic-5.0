//! Modificadores de Atributos (StatModifier - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::stats::stat_enum::StatEnum;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StatModifierType {
    Add,
    Percent,
}

#[derive(Debug, Clone)]
pub struct StatModifier {
    pub stat: StatEnum,
    pub modifier_type: StatModifierType,
    pub value: i32,
    pub source_id: u32,
}

impl StatModifier {
    pub fn add(stat: StatEnum, value: i32, source_id: u32) -> Self {
        Self {
            stat,
            modifier_type: StatModifierType::Add,
            value,
            source_id,
        }
    }

    pub fn percent(stat: StatEnum, value: i32, source_id: u32) -> Self {
        Self {
            stat,
            modifier_type: StatModifierType::Percent,
            value,
            source_id,
        }
    }
}
