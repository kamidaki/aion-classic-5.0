//! Dados para Missões de Ordens de Trabalho / Ofício (WorkOrdersData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct WorkOrdersData {
    pub start_npc_id: u32,
    pub recipe_id: u32,
    pub target_item_id: u32,
    pub count: u64,
}

impl WorkOrdersData {
    pub fn new(start_npc_id: u32, recipe_id: u32, target_item_id: u32, count: u64) -> Self {
        Self {
            start_npc_id,
            recipe_id,
            target_item_id,
            count,
        }
    }
}
