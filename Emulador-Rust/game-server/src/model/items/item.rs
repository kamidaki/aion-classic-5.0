//! Modelo de Item (Item - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::items::item_slot::ItemSlot;
use crate::model::items::manastone::{GodStoneModel, ItemQuality, ManaStoneModel};

#[derive(Debug, Clone)]
pub struct ItemModel {
    pub object_id: u32,
    pub item_id: u32,
    pub count: u64,
    pub quality: ItemQuality,
    pub slot: ItemSlot,
    pub enchant_level: u8,
    pub manastones: Vec<ManaStoneModel>,
    pub godstone: Option<GodStoneModel>,
    pub is_equipped: bool,
}

impl ItemModel {
    pub fn new(object_id: u32, item_id: u32, count: u64, quality: ItemQuality) -> Self {
        Self {
            object_id,
            item_id,
            count,
            quality,
            slot: ItemSlot::MainHand,
            enchant_level: 0,
            manastones: Vec::new(),
            godstone: None,
            is_equipped: false,
        }
    }
}
