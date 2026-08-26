//! Observer de Escudos de Proteção e Barreiras (ShieldObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct ShieldObserver {
    pub shield_id: u32,
    pub radius: f32,
}

impl ShieldObserver {
    pub fn new(shield_id: u32, radius: f32) -> Self {
        Self { shield_id, radius }
    }
}

impl ActionObserver for ShieldObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Move
    }
}
