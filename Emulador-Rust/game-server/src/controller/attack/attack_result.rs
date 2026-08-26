//! Resultado de um Golpe de Ataque (AttackResult - Padrão Java Aion Classic 2.8 / 4.5)

use super::attack_status::AttackStatus;

#[derive(Debug, Clone, Copy)]
pub struct AttackResult {
    pub damage: i32,
    pub attack_status: AttackStatus,
    pub shield_absorbed: i32,
    pub reflected_damage: i32,
}

impl AttackResult {
    pub fn new(damage: i32, attack_status: AttackStatus) -> Self {
        Self {
            damage,
            attack_status,
            shield_absorbed: 0,
            reflected_damage: 0,
        }
    }

    pub fn with_shield(mut self, absorbed: i32) -> Self {
        self.shield_absorbed = absorbed;
        self
    }

    pub fn with_reflection(mut self, reflected: i32) -> Self {
        self.reflected_damage = reflected;
        self
    }
}
