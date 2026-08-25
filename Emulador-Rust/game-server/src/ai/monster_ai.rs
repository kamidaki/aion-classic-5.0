//! IA de Monstros e Combate Ativo (MonsterAI)

use super::abstract_ai::{AbstractAI, BaseAI};
use super::event::AIEvent;
use super::state::{AIState, AISubState};

#[derive(Debug, Clone)]
pub struct MonsterAI {
    pub base: BaseAI,
    pub attack_cooldown: f32,
    pub current_cooldown_timer: f32,
    pub is_ready_to_attack: bool,
}

impl MonsterAI {
    pub fn new(object_id: u32, attack_range: f32, aggro_range: f32, attack_cooldown: f32) -> Self {
        let mut base = BaseAI::new(object_id, attack_range, aggro_range);
        base.state = AIState::Idle;
        Self {
            base,
            attack_cooldown,
            current_cooldown_timer: 0.0,
            is_ready_to_attack: true,
        }
    }

    pub fn on_target_damaged(&mut self, attacker_id: u32, damage: i32) {
        self.base.hate_table.add_damage_hate(attacker_id, damage);
        self.base.target_id = self.base.hate_table.get_highest_target();
        self.base.state = AIState::Attacking;
    }

    pub fn reset(&mut self) {
        self.base.hate_table.clear();
        self.base.target_id = None;
        self.base.state = AIState::Idle;
        self.base.sub_state = AISubState::None;
    }
}

impl AbstractAI for MonsterAI {
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
            AIEvent::Attacked { attacker_id, damage } => {
                self.on_target_damaged(attacker_id, damage);
            }
            AIEvent::TargetLost => {
                if let Some(target) = self.base.target_id {
                    self.base.hate_table.remove_target(target);
                }
                self.base.target_id = self.base.hate_table.get_highest_target();
                if self.base.target_id.is_none() {
                    self.base.state = AIState::Returning;
                }
            }
            AIEvent::Die => {
                self.base.state = AIState::Dead;
                self.base.hate_table.clear();
                self.base.target_id = None;
            }
            AIEvent::Evade => {
                self.base.state = AIState::Evading;
            }
            _ => {}
        }
    }

    fn think(&mut self, dt: f32) {
        if self.base.state == AIState::Attacking {
            if !self.is_ready_to_attack {
                self.current_cooldown_timer -= dt;
                if self.current_cooldown_timer <= 0.0 {
                    self.is_ready_to_attack = true;
                }
            }
        }
    }
}
