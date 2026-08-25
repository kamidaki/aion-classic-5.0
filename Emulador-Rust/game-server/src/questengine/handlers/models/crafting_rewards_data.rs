//! Dados para Missões com Recompensas por Ofício (CraftingRewardsData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct CraftingRewardsData {
    pub start_npc_id: u32,
    pub skill_id: u32,
    pub level_reward: u32,
}

impl CraftingRewardsData {
    pub fn new(start_npc_id: u32, skill_id: u32, level_reward: u32) -> Self {
        Self {
            start_npc_id,
            skill_id,
            level_reward,
        }
    }
}
