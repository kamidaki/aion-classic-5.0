//! Pacotes do Cliente para Produção e Coleta (CM_CRAFT / CM_GATHER - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmCraft {
    pub recipe_id: u32,
    pub target_obj_id: u32,
    pub craft_count: u32,
}

#[derive(Debug, Clone)]
pub struct CmRecipeDelete {
    pub recipe_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmGather {
    pub gatherable_id: u32,
    pub action_type: u8,
}
