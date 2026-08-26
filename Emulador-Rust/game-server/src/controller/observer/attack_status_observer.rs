//! Observer de Status de Ataque (AttackStatusObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone, Default)]
pub struct AttackStatusObserver;

impl ActionObserver for AttackStatusObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Attack
    }
}
