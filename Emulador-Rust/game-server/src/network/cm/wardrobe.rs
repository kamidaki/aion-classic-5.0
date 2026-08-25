//! Pacotes do Cliente para Guarda-Roupa Classic (CM_USER_CLASSIC_WARDROBE_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmUserClassicWardrobeRegister {
    pub item_obj_id: u32,
    pub slot_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmUserClassicWardrobeApply {
    pub slot_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmUserClassicWardrobeDye {
    pub slot_id: u32,
    pub dye_item_id: u32,
}
