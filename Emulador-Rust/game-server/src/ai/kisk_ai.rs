//! IA de Pedras de Ressurreição Kisk (KiskAI - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;
use crate::ai::abstract_ai::{AbstractAI, BaseAI};
use crate::ai::event::AIEventType;
use crate::ai::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct KiskAI {
    pub base: BaseAI,
    pub owner_id: u32,
    pub registered_players: HashSet<u32>,
    pub max_resurrections: u32,
    pub current_resurrections: u32,
    pub max_members: usize,
}

impl KiskAI {
    pub fn new(object_id: u32, owner_id: u32, max_res: u32, max_members: usize) -> Self {
        let mut base = BaseAI::new(object_id, 0.0, 0.0);
        base.state = AIState::Idle;
        let mut registered_players = HashSet::new();
        registered_players.insert(owner_id);

        Self {
            base,
            owner_id,
            registered_players,
            max_resurrections: max_res,
            current_resurrections: 0,
            max_members,
        }
    }

    pub fn register_player(&mut self, player_id: u32) -> Result<(), &'static str> {
        if self.registered_players.len() >= self.max_members {
            return Err("Kisk está lotado");
        }
        self.registered_players.insert(player_id);
        Ok(())
    }

    pub fn use_resurrection(&mut self) -> bool {
        if self.current_resurrections < self.max_resurrections {
            self.current_resurrections += 1;
            if self.current_resurrections >= self.max_resurrections {
                self.base.state = AIState::Dead;
            }
            true
        } else {
            false
        }
    }
}

impl AbstractAI for KiskAI {
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
