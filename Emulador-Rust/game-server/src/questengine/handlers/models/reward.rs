//! Recompensa e Seleção de Itens (Reward - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct QuestReward {
    pub exp: u64,
    pub kinah: u64,
    pub ap: u32,
    pub gp: u32,
    pub reward_items: Vec<(u32, u64)>, // (item_id, count)
}

impl QuestReward {
    pub fn new(exp: u64, kinah: u64, ap: u32, gp: u32) -> Self {
        Self {
            exp,
            kinah,
            ap,
            gp,
            reward_items: Vec::new(),
        }
    }

    pub fn with_item(mut self, item_id: u32, count: u64) -> Self {
        self.reward_items.push((item_id, count));
        self
    }
}
