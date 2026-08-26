//! Observer de Uso de Itens (ItemUseObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct ItemUseObserver {
    pub item_id: u32,
    pub used_count: u32,
}

impl ItemUseObserver {
    pub fn new(item_id: u32) -> Self {
        Self {
            item_id,
            used_count: 0,
        }
    }
}

impl ActionObserver for ItemUseObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::ItemUse
    }

    fn on_item_use(&self, item_id: u32) {
        if item_id == self.item_id {
            println!("[ITEM_USE_OBSERVER] Item #{} utilizado!", item_id);
        }
    }
}
