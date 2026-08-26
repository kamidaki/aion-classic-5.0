//! Serviço de Divisão e Junção de Pilhas de Itens (ItemSplitService).

use crate::data::item::ItemTemplate;

#[derive(Debug, PartialEq, Eq)]
pub enum SplitError {
    NotStackable,
    InvalidQuantity,
    InventoryFull,
}

pub struct ItemSplitService;

impl ItemSplitService {
    pub fn can_split(item: &ItemTemplate, current_amount: u64, split_amount: u64) -> Result<(), SplitError> {
        if !item.is_stackable() {
            return Err(SplitError::NotStackable);
        }
        if split_amount == 0 || split_amount >= current_amount {
            return Err(SplitError::InvalidQuantity);
        }
        Ok(())
    }
}
