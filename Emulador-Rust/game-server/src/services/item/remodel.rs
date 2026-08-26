//! Serviço de Remodelagem de Aparência / Skins (ItemRemodelService).

use crate::data::item::ItemTemplate;

#[derive(Debug, PartialEq, Eq)]
pub enum RemodelError {
    CannotChangeSkin,
    IncompatibleItemCategory,
    InvalidSkinItem,
}

pub struct ItemRemodelService;

impl ItemRemodelService {
    /// Valida se o item principal pode receber a skin de outro item.
    pub fn can_remodel(target: &ItemTemplate, skin_source: &ItemTemplate) -> Result<(), RemodelError> {
        if target.modifiers.cannot_changeskin {
            return Err(RemodelError::CannotChangeSkin);
        }

        // Devem pertencer ao mesmo slot/categoria
        if target.is_weapon() != skin_source.is_weapon() || target.is_armor() != skin_source.is_armor() {
            return Err(RemodelError::IncompatibleItemCategory);
        }

        Ok(())
    }

    /// Retorna o ID visual da nova aparência.
    pub fn get_remodel_visual_id(skin_source: &ItemTemplate) -> u32 {
        skin_source.id
    }
}
