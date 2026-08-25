//! IA de Monstros Agressivos com Auto-Aggro (AggressiveNpcAI)

use super::abstract_ai::AbstractAI;
use super::event::AIEvent;
use super::monster_ai::MonsterAI;
use super::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct AggressiveNpcAI {
    pub monster_ai: MonsterAI,
    pub sight_angle_degrees: f32,
}

impl AggressiveNpcAI {
    pub fn new(object_id: u32, attack_range: f32, aggro_range: f32, attack_cooldown: f32) -> Self {
        Self {
            monster_ai: MonsterAI::new(object_id, attack_range, aggro_range, attack_cooldown),
            sight_angle_degrees: 180.0,
        }
    }

    pub fn check_see_player(&mut self, player_id: u32, distance: f32) -> bool {
        if self.monster_ai.base.state == AIState::Idle || self.monster_ai.base.state == AIState::Walking {
            if distance <= self.monster_ai.base.aggro_range {
                self.monster_ai.base.hate_table.add_damage_hate(player_id, 1);
                self.monster_ai.base.target_id = Some(player_id);
                self.monster_ai.base.state = AIState::Attacking;
                return true;
            }
        }
        false
    }
}

impl AbstractAI for AggressiveNpcAI {
    fn get_state(&self) -> AIState {
        self.monster_ai.get_state()
    }

    fn set_state(&mut self, state: AIState) {
        self.monster_ai.set_state(state);
    }

    fn get_sub_state(&self) -> AISubState {
        self.monster_ai.get_sub_state()
    }

    fn set_sub_state(&mut self, sub_state: AISubState) {
        self.monster_ai.set_sub_state(sub_state);
    }

    fn handle_event(&mut self, event: AIEvent) {
        match event {
            AIEvent::SeePlayer { player_id, distance } => {
                self.check_see_player(player_id, distance);
            }
            _ => self.monster_ai.handle_event(event),
        }
    }

    fn think(&mut self, dt: f32) {
        self.monster_ai.think(dt);
    }
}
