//! Handler de Ativação e Desativação de IA (ActivateEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::state::AIState;

pub struct ActivateEventHandler;

impl ActivateEventHandler {
    pub fn on_activate(current_state: &mut AIState) {
        if *current_state == AIState::Created {
            *current_state = AIState::Idle;
        }
    }

    pub fn on_deactivate(current_state: &mut AIState) {
        *current_state = AIState::Idle;
    }
}
