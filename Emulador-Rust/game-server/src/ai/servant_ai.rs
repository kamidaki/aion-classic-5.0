//! IA de Servos e Totens (ServantAI / TotemAI - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::abstract_ai::{AbstractAI, BaseAI};
use crate::ai::event::AIEventType;
use crate::ai::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct ServantAI {
    pub base: BaseAI,
    pub master_id: u32,
    pub skill_id: u32,
    pub tick_interval_seconds: f32,
    pub current_timer: f32,
    pub lifetime_seconds: f32,
    pub current_lifetime: f32,
}

impl ServantAI {
    pub fn new(object_id: u32, master_id: u32, skill_id: u32, interval: f32, lifetime: f32) -> Self {
        let mut base = BaseAI::new(object_id, 15.0, 15.0);
        base.state = AIState::Idle;
        Self {
            base,
            master_id,
            skill_id,
            tick_interval_seconds: interval,
            current_timer: 0.0,
            lifetime_seconds: lifetime,
            current_lifetime: 0.0,
        }
    }

    /// Processa o tick periódico de ataque ou cura do servo
    pub fn tick_servant(&mut self, dt: f32) -> Option<u32> {
        self.current_lifetime += dt;
        if self.current_lifetime >= self.lifetime_seconds {
            self.base.state = AIState::Dead;
            return None;
        }

        self.current_timer += dt;
        if self.current_timer >= self.tick_interval_seconds {
            self.current_timer = 0.0;
            Some(self.skill_id)
        } else {
            None
        }
    }
}

impl AbstractAI for ServantAI {
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

    fn think(&mut self, dt: f32) {
        self.tick_servant(dt);
    }
}
