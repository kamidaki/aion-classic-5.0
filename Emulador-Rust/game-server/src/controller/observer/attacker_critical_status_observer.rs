//! Observer de Status Crítico (AttackerCriticalStatusObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::attacker_critical_status::AttackerCriticalStatus;
use super::observer_type::ObserverType;

#[derive(Debug, Clone, Default)]
pub struct AttackerCriticalStatusObserver {
    pub status: AttackerCriticalStatus,
}

impl ActionObserver for AttackerCriticalStatusObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Attack
    }
}
