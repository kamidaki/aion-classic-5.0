//! Modelos de Receitas e Produção Artesanal (CraftRecipe - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct CraftRecipeModel {
    pub id: u32,
    pub skill_id: u32,
    pub required_skill_level: u32,
    pub product_item_id: u32,
    pub product_count: u32,
    pub critical_product_item_id: Option<u32>,
    pub required_materials: Vec<(u32, u32)>, // (item_id, count)
}

impl CraftRecipeModel {
    pub fn new(id: u32, skill_id: u32, skill_level: u32, product_id: u32, count: u32) -> Self {
        Self {
            id,
            skill_id,
            required_skill_level: skill_level,
            product_item_id: product_id,
            product_count: count,
            critical_product_item_id: None,
            required_materials: Vec::new(),
        }
    }
}
