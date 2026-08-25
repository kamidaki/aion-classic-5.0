//! Locais de Siege e Fortalezas (SiegeLocation / SiegeState - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SiegeState {
    Peaceful,
    Vulnerable,
}

#[derive(Debug, Clone)]
pub struct SiegeLocation {
    pub id: u32,
    pub name: String,
    pub state: SiegeState,
    pub occupying_legion_id: Option<u32>,
    pub deity_hp: i32,
}

impl SiegeLocation {
    pub fn new(id: u32, name: &str) -> Self {
        Self {
            id,
            name: name.to_string(),
            state: SiegeState::Peaceful,
            occupying_legion_id: None,
            deity_hp: 1_000_000,
        }
    }

    pub fn start_siege(&mut self) {
        self.state = SiegeState::Vulnerable;
        self.deity_hp = 1_000_000;
    }

    pub fn resolve_siege(&mut self, winning_legion_id: Option<u32>) {
        self.occupying_legion_id = winning_legion_id;
        self.state = SiegeState::Peaceful;
    }
}
