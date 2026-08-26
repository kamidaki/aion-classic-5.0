//! Pacote SM_ADD_INVENTORY

#[derive(Debug, Clone)]
pub struct SmAddInventory {
    pub item_obj_id: u32,
    pub item_id: u32,
    pub count: u64,
    pub slot: u16,
}
