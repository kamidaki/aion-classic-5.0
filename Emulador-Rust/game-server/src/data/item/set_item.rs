//! Bônus de conjuntos de itens (Item Sets) do Aion Classic.

use std::collections::HashMap;

#[derive(Debug, Clone, Default)]
pub struct SetBonus {
    pub stats: HashMap<String, i32>,
}

#[derive(Debug, Clone, Default)]
pub struct SetItemTemplate {
    pub id: u32,
    pub name: String,
    pub desc: String,
    pub item_names: Vec<String>,
    pub piece_bonuses: HashMap<u8, SetBonus>, // ex: 2 -> bônus de 2 peças, 3 -> 3 peças
    pub fullset_bonus: Option<SetBonus>,
}

impl SetItemTemplate {
    pub fn new(id: u32, name: String, desc: String) -> Self {
        Self {
            id,
            name,
            desc,
            item_names: Vec::new(),
            piece_bonuses: HashMap::new(),
            fullset_bonus: None,
        }
    }
}
