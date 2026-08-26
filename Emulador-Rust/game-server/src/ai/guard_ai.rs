//! IA de Guardas de Cidade e Fortalezas (GuardAI - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::abstract_ai::AbstractAI;
use crate::ai::event::AIEventType;
use crate::ai::monster_ai::MonsterAI;
use crate::ai::state::{AIState, AISubState};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Faction {
    Elyos,
    Asmodians,
    Balaur,
}

#[derive(Debug, Clone)]
pub struct GuardAI {
    pub monster_ai: MonsterAI,
    pub guard_faction: Faction,
}

impl GuardAI {
    pub fn new(object_id: u32, guard_faction: Faction, attack_range: f32, aggro_range: f32) -> Self {
        Self {
            monster_ai: MonsterAI::new(object_id, attack_range, aggro_range, 1.5),
            guard_faction,
        }
    }

    pub fn check_enemy_player(&mut self, player_id: u32, player_faction: Faction, distance: f32) -> bool {
        if self.is_hostile(player_faction) && distance <= self.monster_ai.base.aggro_range {
            if self.monster_ai.base.state == AIState::Idle || self.monster_ai.base.state == AIState::Walking {
                self.monster_ai.base.hate_table.add_damage_hate(player_id, 100);
                self.monster_ai.base.target_id = Some(player_id);
                self.monster_ai.base.state = AIState::Attacking;
                return true;
            }
        }
        false
    }

    pub fn is_hostile(&self, other_faction: Faction) -> bool {
        self.guard_faction != other_faction
    }
}

impl AbstractAI for GuardAI {
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

    fn handle_event(&mut self, event: AIEventType) {
        self.monster_ai.handle_event(event);
    }

    fn think(&mut self, dt: f32) {
        self.monster_ai.think(dt);
    }
}
