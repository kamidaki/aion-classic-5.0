//! Pedras de Mana, Pedras Divinas e Qualidades (ManaStone / GodStone / ItemQuality - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::stats::stat_enum::StatEnum;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ItemQuality {
    #[default]
    Junk,
    Common,
    Rare,
    Legendary,
    Unique,
    Epic,
    Mythic,
}

#[derive(Debug, Clone)]
pub struct ManaStoneModel {
    pub item_id: u32,
    pub stat: StatEnum,
    pub value: i32,
}

#[derive(Debug, Clone)]
pub struct GodStoneModel {
    pub item_id: u32,
    pub skill_id: u32,
    pub probability: f32, // Ex: 0.05 (5%)
    pub damage: u32,
}
