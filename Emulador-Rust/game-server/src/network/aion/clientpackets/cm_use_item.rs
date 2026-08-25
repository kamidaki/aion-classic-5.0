//! Pacote CM_USE_ITEM (Opcode 0x0026)

#[derive(Debug, Clone)]
pub struct CmUseItem {
    pub item_obj_id: u32,
    pub target_obj_id: Option<u32>,
}
