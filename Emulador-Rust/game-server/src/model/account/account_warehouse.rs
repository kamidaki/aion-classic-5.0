//! Armazém Compartilhado de Conta (AccountWarehouse - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;

#[derive(Debug, Clone, Default)]
pub struct AccountWarehouseModel {
    pub account_id: u32,
    pub max_slots: u8,
    pub items: HashMap<u8, (u32, u32)>, // slot -> (item_id, count)
    pub kinah: u64,
}

impl AccountWarehouseModel {
    pub fn new(account_id: u32, max_slots: u8) -> Self {
        Self {
            account_id,
            max_slots,
            items: HashMap::new(),
            kinah: 0,
        }
    }

    pub fn deposit_item(&mut self, slot: u8, item_id: u32, count: u32) -> Result<(), &'static str> {
        if slot >= self.max_slots {
            return Err("Slot excede o limite do armazém de conta");
        }
        self.items.insert(slot, (item_id, count));
        Ok(())
    }

    pub fn withdraw_item(&mut self, slot: u8) -> Option<(u32, u32)> {
        self.items.remove(&slot)
    }
}
