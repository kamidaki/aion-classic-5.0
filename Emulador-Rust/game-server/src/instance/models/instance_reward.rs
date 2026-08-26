//! Recompensas e Pontuações de Instâncias (InstanceReward / InstanceScore - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Default)]
pub struct InstanceReward {
    pub abyss_points: u32,
    pub glory_points: u32,
    pub kinah: u64,
    pub exp: u64,
    pub reward_items: Vec<(u32, u32)>, // (item_id, count)
}

impl InstanceReward {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_item(&mut self, item_id: u32, count: u32) {
        self.reward_items.push((item_id, count));
    }
}

#[derive(Debug, Clone, Default)]
pub struct InstanceScore {
    pub points: i32,
    pub monsters_killed: u32,
    pub bosses_killed: u32,
    pub deaths: u32,
}

impl InstanceScore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_kill(&mut self, is_boss: bool, pts: i32) {
        if is_boss {
            self.bosses_killed += 1;
        } else {
            self.monsters_killed += 1;
        }
        self.points = self.points.saturating_add(pts);
    }

    pub fn record_death(&mut self) {
        self.deaths += 1;
        self.points = self.points.saturating_sub(200);
    }

    pub fn get_rank(&self) -> char {
        if self.points >= 15_000 {
            'S'
        } else if self.points >= 10_000 {
            'A'
        } else if self.points >= 6_000 {
            'B'
        } else if self.points >= 3_000 {
            'C'
        } else {
            'F'
        }
    }
}
