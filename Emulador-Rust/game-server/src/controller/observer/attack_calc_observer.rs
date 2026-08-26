//! Observer de Modificação de Cálculo de Ataque (AttackCalcObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct AttackCalcObserver {
    pub boost_percent: f32,
    pub is_active: bool,
}

impl AttackCalcObserver {
    pub fn new(boost_percent: f32) -> Self {
        Self {
            boost_percent,
            is_active: true,
        }
    }

    pub fn apply_boost(&self, original_damage: i32) -> i32 {
        if self.is_active {
            (original_damage as f32 * (1.0 + self.boost_percent / 100.0)) as i32
        } else {
            original_damage
        }
    }
}

impl ActionObserver for AttackCalcObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Attack
    }
}
