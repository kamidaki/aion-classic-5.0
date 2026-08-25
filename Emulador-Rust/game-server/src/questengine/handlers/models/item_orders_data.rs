//! Dados para Missões de Pedidos de Entregas de Itens (ItemOrdersData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct ItemOrdersData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub item_id: u32,
    pub count: u64,
}

impl ItemOrdersData {
    pub fn new(start_npc_id: u32, end_npc_id: u32, item_id: u32, count: u64) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            item_id,
            count,
        }
    }
}
