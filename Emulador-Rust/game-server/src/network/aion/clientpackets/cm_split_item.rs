//! Pacote CM_SPLIT_ITEM

#[derive(Debug, Clone)]
pub struct CmSplitItem {
    pub item_obj_id: u32,
    pub split_count: u64,
    pub target_slot: u16,
}
