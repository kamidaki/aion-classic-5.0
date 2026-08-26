//! Template completo de item do Aion Classic.

use super::slot::ItemSlot;
use super::quality::ItemQuality;
use super::weapon::WeaponType;
use super::armor::ArmorType;
use super::accessory::AccessoryType;
use super::stats::ItemStats;
use super::restrictions::ItemRestrictions;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ItemCategory {
    #[default]
    Normal,
    Weapon,
    Armor,
    Accessory,
    Consumable,
    Quest,
    Crafting,
    Stigma,
    Dye,
    Kinah,
    Skin,
}

#[derive(Debug, Clone, Default)]
pub struct ItemModifiers {
    pub option_slot_bonus: u8,    // Slots de Manastone (Pedras de Mana)
    pub no_enchant: bool,         // Se não pode ser encantado
    pub can_proc_enchant: bool,   // Se suporta enchant procs
    pub can_composite: bool,      // Se suporta fusão de 2 mãos (Armsfusion)
    pub cannot_changeskin: bool,  // Se não pode sofrer remodelagem cosmética
    pub dye: bool,                // Se permite pintura/dye
    pub soul_bind: bool,          // Vinculação à alma ao equipar
    pub charge_capacity: u32,     // Capacidade de potencializador / conditioning
    pub max_enchant_level: u8,    // Limite máximo de encantamento (padrão: 15)
}

#[derive(Debug, Clone, Default)]
pub struct ItemTemplate {
    pub id: u32,
    pub name: String,
    pub clean_name: String,       // Nome real do item decodificado do strings XML
    pub desc: String,             // Chave da string (ex: STR_SWORD_CIRCULOUS)
    pub category: ItemCategory,
    pub quality: ItemQuality,
    pub slot: ItemSlot,
    pub weapon_type: Option<WeaponType>,
    pub armor_type: Option<ArmorType>,
    pub accessory_type: Option<AccessoryType>,
    pub level: u8,
    pub price: u64,
    pub max_stack_count: u32,
    pub mask: u16,                // Máscara de direitos (vender, trocar, depositar)
    pub stats: ItemStats,
    pub restrictions: ItemRestrictions,
    pub modifiers: ItemModifiers,
}

impl ItemTemplate {
    pub fn new(id: u32, name: String) -> Self {
        Self {
            id,
            name: name.clone(),
            clean_name: name,
            max_stack_count: 1,
            ..Default::default()
        }
    }

    #[inline]
    pub fn is_weapon(&self) -> bool {
        self.weapon_type.is_some() || self.slot.is_weapon()
    }

    #[inline]
    pub fn is_two_handed(&self) -> bool {
        self.weapon_type.map(|w| w.is_two_handed()).unwrap_or(false)
    }

    #[inline]
    pub fn is_armor(&self) -> bool {
        self.armor_type.is_some() || self.slot.is_armor_body()
    }

    #[inline]
    pub fn is_wings(&self) -> bool {
        self.slot.contains(ItemSlot::WINGS)
    }

    #[inline]
    pub fn is_skin(&self) -> bool {
        self.modifiers.cannot_changeskin
    }

    #[inline]
    pub fn is_stackable(&self) -> bool {
        self.max_stack_count > 1
    }

    #[inline]
    pub fn can_be_equipped_by(&self, class_id: u8, level: u8) -> bool {
        level >= self.restrictions.min_level && self.restrictions.class_mask.allows(class_id)
    }
}
