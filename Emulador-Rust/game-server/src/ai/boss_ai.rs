//! IA de Chefes de Masmorra com 4 Fases Dinâmicas (BossAI)

use super::abstract_ai::AbstractAI;
use super::event::AIEvent;
use super::monster_ai::MonsterAI;
use super::state::{AIState, AISubState};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BossPhase {
    Phase1Normal,
    Phase2Adds,
    Phase3AoECast,
    Phase4Enrage,
}

#[derive(Debug, Clone)]
pub struct BossAI {
    pub monster_ai: MonsterAI,
    pub current_phase: BossPhase,
    pub adds_spawned: bool,
    pub aoe_casted: bool,
    pub is_enraged: bool,
    pub damage_multiplier: f32,
    pub attack_speed_multiplier: f32,
}

impl BossAI {
    pub fn new(object_id: u32, attack_range: f32, aggro_range: f32, attack_cooldown: f32) -> Self {
        Self {
            monster_ai: MonsterAI::new(object_id, attack_range, aggro_range, attack_cooldown),
            current_phase: BossPhase::Phase1Normal,
            adds_spawned: false,
            aoe_casted: false,
            is_enraged: false,
            damage_multiplier: 1.0,
            attack_speed_multiplier: 1.0,
        }
    }

    pub fn update_hp_phase(&mut self, current_hp_percent: f32) -> Option<BossPhase> {
        let old_phase = self.current_phase;

        if current_hp_percent <= 25.0 {
            self.current_phase = BossPhase::Phase4Enrage;
            self.is_enraged = true;
            self.damage_multiplier = 2.0; // +100% de dano
            self.attack_speed_multiplier = 1.5; // +50% de velocidade
        } else if current_hp_percent <= 50.0 {
            self.current_phase = BossPhase::Phase3AoECast;
            self.aoe_casted = true;
        } else if current_hp_percent <= 75.0 {
            self.current_phase = BossPhase::Phase2Adds;
            self.adds_spawned = true;
        } else {
            self.current_phase = BossPhase::Phase1Normal;
        }

        if self.current_phase != old_phase {
            Some(self.current_phase)
        } else {
            None
        }
    }
}

impl AbstractAI for BossAI {
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
            AIEvent::HpPhaseChange { current_hp_percent } => {
                self.update_hp_phase(current_hp_percent);
            }
            _ => self.monster_ai.handle_event(event),
        }
    }

    fn think(&mut self, dt: f32) {
        self.monster_ai.think(dt);
    }
}
