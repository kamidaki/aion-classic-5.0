//! Pacotes do Servidor para Produção e Coleta (SM_RECIPE_* / SM_GATHER_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct SmRecipeList {
    pub player_id: u32,
    pub recipe_ids: Vec<u32>,
}

#[derive(Debug, Clone)]
pub struct SmAddRecipe {
    pub recipe_id: u32,
}

#[derive(Debug, Clone)]
pub struct SmRemoveRecipe {
    pub recipe_id: u32,
}

#[derive(Debug, Clone)]
pub struct SmGather {
    pub gatherable_id: u32,
    pub player_id: u32,
    pub success: bool,
}
