//! Pacote SM_ITEM_LIST / SM_LOAD_INVENTORY (Opcode 0x001B)

#[derive(Debug, Clone)]
pub struct SmItemList {
    pub total_items: u16,
}
