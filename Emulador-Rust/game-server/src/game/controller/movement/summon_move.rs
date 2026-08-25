//! SummonMoveController - Movimentação de invocações (Espíritos)

use super::creature_move::CreatureMoveController;

#[derive(Debug, Clone)]
pub struct SummonMoveController {
    pub creature_move: CreatureMoveController,
    pub master_id: u32,
    pub follow_distance: f32,
}

impl SummonMoveController {
    pub fn new(x: f32, y: f32, z: f32, heading: u8, speed: f32, master_id: u32) -> Self {
        Self {
            creature_move: CreatureMoveController::new(x, y, z, heading, speed),
            master_id,
            follow_distance: 3.0,
        }
    }

    pub fn update_follow(&mut self, master_x: f32, master_y: f32, master_z: f32, dt: f32) {
        let dist = self.creature_move.distance_to(master_x, master_y, master_z);
        if dist > self.follow_distance {
            let step = self.creature_move.speed * dt;
            let ratio = (step / dist).min(1.0);
            let nx = self.creature_move.x + (master_x - self.creature_move.x) * ratio;
            let ny = self.creature_move.y + (master_y - self.creature_move.y) * ratio;
            let nz = self.creature_move.z + (master_z - self.creature_move.z) * ratio;
            self.creature_move.set_position(nx, ny, nz, self.creature_move.heading);
            self.creature_move.is_moving = true;
        } else {
            self.creature_move.is_moving = false;
        }
    }
}
