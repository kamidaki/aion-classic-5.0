//! PlayerController - Gerenciador completo de ações do jogador

use super::creature::CreatureController;

#[derive(Debug, Clone)]
pub struct PlayerController {
    pub creature: CreatureController,
    pub account_id: u32,
    pub is_flying: bool,
    pub flight_time_remaining: u32,
    pub max_flight_time: u32,
    pub is_gliding: bool,
}

impl PlayerController {
    pub fn new(player_id: u32, account_id: u32, max_hp: i32, max_mp: u32, max_flight_time: u32) -> Self {
        Self {
            creature: CreatureController::new(player_id, max_hp, max_mp),
            account_id,
            is_flying: false,
            flight_time_remaining: max_flight_time,
            max_flight_time,
            is_gliding: false,
        }
    }

    pub fn start_fly(&mut self) -> bool {
        if self.flight_time_remaining > 0 && !self.creature.is_dead {
            self.is_flying = true;
            self.is_gliding = false;
            true
        } else {
            false
        }
    }

    pub fn stop_fly(&mut self) {
        self.is_flying = false;
        self.is_gliding = false;
    }

    pub fn toggle_glide(&mut self) -> bool {
        if !self.creature.is_dead {
            self.is_gliding = !self.is_gliding;
            self.is_gliding
        } else {
            false
        }
    }

    pub fn tick_flight(&mut self, seconds: u32) {
        if self.is_flying || self.is_gliding {
            self.flight_time_remaining = self.flight_time_remaining.saturating_sub(seconds);
            if self.flight_time_remaining == 0 {
                self.stop_fly();
            }
        }
    }

    pub fn restore_flight_time(&mut self, amount: u32) {
        self.flight_time_remaining = (self.flight_time_remaining + amount).min(self.max_flight_time);
    }
}
