//! PlayerMoveController - Validação de coordenadas do cliente, anti-speedhack e vetores

use super::playable_move::PlayableMoveController;

#[derive(Debug, Clone)]
pub struct PlayerMoveController {
    pub playable_move: PlayableMoveController,
    pub target_x: f32,
    pub target_y: f32,
    pub target_z: f32,
    pub vector_x: f32,
    pub vector_y: f32,
    pub vector_z: f32,
}

impl PlayerMoveController {
    pub fn new(x: f32, y: f32, z: f32, heading: u8, speed: f32) -> Self {
        Self {
            playable_move: PlayableMoveController::new(x, y, z, heading, speed),
            target_x: x,
            target_y: y,
            target_z: z,
            vector_x: 0.0,
            vector_y: 0.0,
            vector_z: 0.0,
        }
    }

    pub fn validate_move(
        &mut self,
        new_x: f32,
        new_y: f32,
        new_z: f32,
        heading: u8,
        dt_seconds: f32,
    ) -> bool {
        let dist = self.playable_move.creature_move.distance_to(new_x, new_y, new_z);
        let max_allowed_dist = (self.playable_move.creature_move.speed * dt_seconds * 1.5).max(3.0);

        if dist <= max_allowed_dist {
            self.playable_move.creature_move.set_position(new_x, new_y, new_z, heading);
            self.target_x = new_x;
            self.target_y = new_y;
            self.target_z = new_z;
            true
        } else {
            false // Potencial Speedhack / Desync
        }
    }
}
