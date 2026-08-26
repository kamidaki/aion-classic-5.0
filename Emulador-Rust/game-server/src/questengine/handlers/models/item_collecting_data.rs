//! Dados para Template de Coleta de Itens (ItemCollectingData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct ItemCollectingData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub items: Vec<(u32, u64)>, // (item_id, count)
}

impl ItemCollectingData {
    pub fn new(start_npc_id: u32, end_npc_id: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            items: Vec::new(),
        }
    }

    pub fn with_item(mut self, item_id: u32, count: u64) -> Self {
        self.items.push((item_id, count));
        self
    }
}
