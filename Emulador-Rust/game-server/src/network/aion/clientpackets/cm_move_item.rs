//! Pacote CM_MOVE_ITEM

#[derive(Debug, Clone)]
pub struct CmMoveItem {
    pub item_obj_id: u32,
    pub source_storage_type: u8,
    pub target_storage_type: u8,
    pub target_slot: u16,
}
