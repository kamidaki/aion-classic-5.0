//! Pacote SM_RECIPE_LIST

#[derive(Debug, Clone)]
pub struct SmRecipeList {
    pub player_id: u32,
    pub recipe_ids: Vec<u32>,
}
