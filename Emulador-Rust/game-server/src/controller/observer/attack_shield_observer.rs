//! Observer de Escudo e Absorção de Dano (AttackShieldObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct AttackShieldObserver {
    pub shield_hp: i32,
    pub max_shield_hp: i32,
    pub percent_reduction: u8,
}

impl AttackShieldObserver {
    pub fn new(max_shield_hp: i32, percent_reduction: u8) -> Self {
        Self {
            shield_hp: max_shield_hp,
            max_shield_hp,
            percent_reduction,
        }
    }

    pub fn absorb_damage(&mut self, damage: i32) -> (i32, i32) {
        if self.shield_hp <= 0 {
            return (damage, 0);
        }

        let portion = (damage as f32 * (self.percent_reduction as f32 / 100.0)) as i32;
        let absorbed = portion.min(self.shield_hp);
        self.shield_hp = self.shield_hp.saturating_sub(absorbed);
        let remaining_dmg = damage - absorbed;

        (remaining_dmg, absorbed)
    }

    pub fn is_broken(&self) -> bool {
        self.shield_hp <= 0
    }
}

impl ActionObserver for AttackShieldObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Attacked
    }
}
