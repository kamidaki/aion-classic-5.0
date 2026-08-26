//! Pacote CM_ENCHANMENT_STONES

#[derive(Debug, Clone)]
pub struct CmEnchantmentStones {
    pub target_item_obj_id: u32,
    pub stone_item_obj_id: u32,
    pub supplement_item_obj_id: Option<u32>,
}
