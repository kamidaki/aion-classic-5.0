//! Handler de Diálogo de NPCs e Interações (TalkEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::state::AIState;

pub struct TalkEventHandler;

impl TalkEventHandler {
    pub fn on_talk(state: &mut AIState) {
        if *state == AIState::Idle || *state == AIState::Walking {
            *state = AIState::Talking;
        }
    }

    pub fn on_finish_talk(state: &mut AIState) {
        if *state == AIState::Talking {
            *state = AIState::Idle;
        }
    }
}
