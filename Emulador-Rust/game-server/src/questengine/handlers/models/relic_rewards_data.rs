//! Dados para Troca de Relíquias do Abyss por AP (RelicRewardsData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct RelicRewardsData {
    pub relic_npc_id: u32,
    pub relic_item_id: u32,
    pub reward_ap: u32,
}

impl RelicRewardsData {
    pub fn new(relic_npc_id: u32, relic_item_id: u32, reward_ap: u32) -> Self {
        Self {
            relic_npc_id,
            relic_item_id,
            reward_ap,
        }
    }
}
