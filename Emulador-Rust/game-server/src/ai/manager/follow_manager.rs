//! Gerenciador de Acompanhamento (FollowManager - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::ai::follow::follow_service::FollowStartService;

#[derive(Debug, Clone)]
pub struct FollowManager {
    pub target_id: Option<u32>,
    pub follow_range: f32,
    pub speed: f32,
}

impl FollowManager {
    pub fn new(follow_range: f32, speed: f32) -> Self {
        Self {
            target_id: None,
            follow_range,
            speed,
        }
    }

    pub fn set_follow_target(&mut self, target_id: u32) {
        self.target_id = Some(target_id);
    }

    pub fn stop_follow(&mut self) {
        self.target_id = None;
    }

    pub fn tick_follow(&self, current_pos: &Coord, target_pos: &Coord, dt: f32) -> Coord {
        if FollowStartService::should_follow(current_pos, target_pos, self.follow_range) {
            FollowStartService::calculate_step(current_pos, target_pos, self.speed, dt)
        } else {
            *current_pos
        }
    }
}
