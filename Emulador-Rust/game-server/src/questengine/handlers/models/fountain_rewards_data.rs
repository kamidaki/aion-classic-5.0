//! Dados para Missões de Oferendas em Fontes Mágicas (FountainRewardsData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct FountainRewardsData {
    pub fountain_npc_id: u32,
    pub medal_item_id: u32,
    pub reward_item_id: u32,
}

impl FountainRewardsData {
    pub fn new(fountain_npc_id: u32, medal_item_id: u32, reward_item_id: u32) -> Self {
        Self {
            fountain_npc_id,
            medal_item_id,
            reward_item_id,
        }
    }
}
