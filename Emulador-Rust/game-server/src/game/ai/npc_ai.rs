//! IA de NPCs Pacíficos e Interativos (NpcAI)

use super::abstract_ai::{AbstractAI, BaseAI};
use super::event::AIEvent;
use super::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct NpcAI {
    pub base: BaseAI,
    pub is_dialog_open: bool,
    pub active_interactor: Option<u32>,
}

impl NpcAI {
    pub fn new(object_id: u32) -> Self {
        let mut base = BaseAI::new(object_id, 2.0, 0.0);
        base.state = AIState::Idle;
        Self {
            base,
            is_dialog_open: false,
            active_interactor: None,
        }
    }

    pub fn open_dialog(&mut self, player_id: u32) {
        self.is_dialog_open = true;
        self.active_interactor = Some(player_id);
    }

    pub fn close_dialog(&mut self) {
        self.is_dialog_open = false;
        self.active_interactor = None;
    }
}

impl AbstractAI for NpcAI {
    fn get_state(&self) -> AIState {
        self.base.state
    }

    fn set_state(&mut self, state: AIState) {
        self.base.state = state;
    }

    fn get_sub_state(&self) -> AISubState {
        self.base.sub_state
    }

    fn set_sub_state(&mut self, sub_state: AISubState) {
        self.base.sub_state = sub_state;
    }

    fn handle_event(&mut self, event: AIEvent) {
        match event {
            AIEvent::Spawn => self.base.state = AIState::Idle,
            AIEvent::Die => self.base.state = AIState::Dead,
            _ => {}
        }
    }

    fn think(&mut self, _dt: f32) {
        // NPCs pacíficos mantêm estado Idle
    }
}
