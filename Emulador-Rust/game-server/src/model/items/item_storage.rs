//! Armazenamento de Itens e Inventário (ItemStorage / StorageType - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::model::items::item::ItemModel;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum StorageType {
    #[default]
    Cube,
    RegularWarehouse,
    AccountWarehouse,
    LegionWarehouse,
    PetBag,
    Mailbox,
}

#[derive(Debug, Clone)]
pub struct ItemStorageModel {
    pub storage_type: StorageType,
    pub max_capacity: u16,
    pub items: HashMap<u16, ItemModel>, // slot -> ItemModel
    pub kinah: u64,
}

impl ItemStorageModel {
    pub fn new(storage_type: StorageType, capacity: u16) -> Self {
        Self {
            storage_type,
            max_capacity: capacity,
            items: HashMap::new(),
            kinah: 0,
        }
    }

    pub fn add_item(&mut self, slot: u16, item: ItemModel) -> Result<(), &'static str> {
        if slot >= self.max_capacity {
            return Err("Inventário/Armazém cheio");
        }
        self.items.insert(slot, item);
        Ok(())
    }

    pub fn remove_item(&mut self, slot: u16) -> Option<ItemModel> {
        self.items.remove(&slot)
    }

    pub fn item_count(&self) -> usize {
        self.items.len()
    }
}
