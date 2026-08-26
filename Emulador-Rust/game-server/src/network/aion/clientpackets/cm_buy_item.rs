//! Pacote CM_BUY_ITEM

#[derive(Debug, Clone)]
pub struct CmBuyItem {
    pub seller_obj_id: u32,
    pub item_id: u32,
    pub count: u64,
}
