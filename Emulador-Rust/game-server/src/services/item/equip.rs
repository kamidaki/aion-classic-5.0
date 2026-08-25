//! Serviço de Equipamento e Desequipamento de Itens (ItemEquipService).
//! Validações de Classe, Nível, Raça, Gênero, Slots de Mãos (1H / 2H / Dual Wield) e Armaduras.

use crate::character::Character;
use crate::data::item::{ItemSlot, ItemTemplate};

#[derive(Debug, PartialEq, Eq)]
pub enum EquipError {
    ItemNotFound,
    LevelTooLow { required: u8, current: u8 },
    ClassNotAllowed,
    RaceNotAllowed,
    GenderNotAllowed,
    InvalidSlot,
    SlotOccupied,
}

pub struct ItemEquipService;

impl ItemEquipService {
    /// Valida se o personagem pode vestir o item conforme as regras de negócio oficiais.
    pub fn can_equip(character: &Character, item: &ItemTemplate, target_slot: ItemSlot) -> Result<(), EquipError> {
        let char_level = character.stats.level as u8;
        if char_level < item.restrictions.min_level {
            return Err(EquipError::LevelTooLow {
                required: item.restrictions.min_level,
                current: char_level,
            });
        }

        // Validação de classe
        let class_id = character.class_id();
        if !item.restrictions.class_mask.allows(class_id) {
            return Err(EquipError::ClassNotAllowed);
        }

        // Validação de raça
        let char_race = character.race();
        match item.restrictions.race {
            crate::data::item::RacePermitted::Elyos if char_race != 0 => return Err(EquipError::RaceNotAllowed),
            crate::data::item::RacePermitted::Asmodian if char_race != 1 => return Err(EquipError::RaceNotAllowed),
            _ => {}
        }

        // Validação de gênero
        let char_gender = character.gender();
        match item.restrictions.gender {
            crate::data::item::GenderPermitted::Male if char_gender != 0 => return Err(EquipError::GenderNotAllowed),
            crate::data::item::GenderPermitted::Female if char_gender != 1 => return Err(EquipError::GenderNotAllowed),
            _ => {}
        }

        // Validação de compatibilidade de slot
        if !item.slot.intersects(target_slot) {
            return Err(EquipError::InvalidSlot);
        }

        Ok(())
    }

    /// Processa o equipamento de uma arma de duas mãos ou empunhadura dupla (Dual-Wielding).
    pub fn is_two_handed(item: &ItemTemplate) -> bool {
        item.is_two_handed()
    }
}
