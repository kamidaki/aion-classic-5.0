//! Observer de Diálogos com NPCs (DialogObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct DialogObserver {
    pub target_npc_id: u32,
    pub is_active: bool,
}

impl DialogObserver {
    pub fn new(target_npc_id: u32) -> Self {
        Self {
            target_npc_id,
            is_active: true,
        }
    }
}

impl ActionObserver for DialogObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Dialog
    }

    fn on_dialog(&self, target_id: u32) {
        if target_id == self.target_npc_id {
            println!("[DIALOG_OBSERVER] Interagiu com NPC #{}", target_id);
        }
    }
}
