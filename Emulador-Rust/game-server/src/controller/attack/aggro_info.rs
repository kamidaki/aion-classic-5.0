//! Informações de Ameaça/Ódio de um Atacante (AggroInfo - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct AggroInfo {
    pub attacker_id: u32,
    pub hate: i32,
    pub damage: i32,
}

impl AggroInfo {
    pub fn new(attacker_id: u32) -> Self {
        Self {
            attacker_id,
            hate: 1,
            damage: 0,
        }
    }

    pub fn add_hate(&mut self, amount: i32) {
        self.hate = self.hate.saturating_add(amount);
    }

    pub fn add_damage(&mut self, amount: i32) {
        self.damage = self.damage.saturating_add(amount);
        self.add_hate(amount);
    }
}
