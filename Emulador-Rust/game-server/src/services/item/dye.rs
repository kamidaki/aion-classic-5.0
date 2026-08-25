//! Serviço de Tinturas e Pintura de Armaduras (ItemDyeService).

use crate::data::item::{DyeColorTemplate, ItemTemplate, RgbColor};

#[derive(Debug, PartialEq, Eq)]
pub enum DyeError {
    NotDyeable,
    InvalidDyeItem,
}

pub struct ItemDyeService;

impl ItemDyeService {
    /// Valida se a armadura pode ser tingida.
    pub fn can_dye(item: &ItemTemplate) -> Result<(), DyeError> {
        if !item.modifiers.dye && !item.is_armor() {
            return Err(DyeError::NotDyeable);
        }
        Ok(())
    }

    /// Aplica a cor da tintura na peça de equipamento.
    pub fn apply_dye(_item: &ItemTemplate, dye_template: &DyeColorTemplate) -> Result<RgbColor, DyeError> {
        Ok(dye_template.color)
    }
}
