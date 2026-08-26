//! IA de Armadilhas (TrapAI - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::abstract_ai::{AbstractAI, BaseAI};
use crate::ai::event::AIEventType;
use crate::ai::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct TrapAI {
    pub base: BaseAI,
    pub owner_id: u32,
    pub trigger_radius: f32,
    pub skill_id: u16,
    pub is_triggered: bool,
}

impl TrapAI {
    pub fn new(object_id: u32, owner_id: u32, trigger_radius: f32, skill_id: u16) -> Self {
        let mut base = BaseAI::new(object_id, 0.0, trigger_radius);
        base.state = AIState::Idle;
        Self {
            base,
            owner_id,
            trigger_radius,
            skill_id,
            is_triggered: false,
        }
    }

    pub fn check_trigger(&mut self, entity_id: u32, distance: f32) -> Option<u16> {
        if self.is_triggered || entity_id == self.owner_id {
            return None;
        }

        if distance <= self.trigger_radius {
            self.is_triggered = true;
            self.base.state = AIState::Dead;
            Some(self.skill_id)
        } else {
            None
        }
    }
}

impl AbstractAI for TrapAI {
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

    fn handle_event(&mut self, event: AIEventType) {
        if let AIEventType::Died = event {
            self.base.state = AIState::Dead;
        }
    }

    fn think(&mut self, _dt: f32) {}
}
