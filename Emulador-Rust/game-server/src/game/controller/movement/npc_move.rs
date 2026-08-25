//! NpcMoveController - Roteamento de NPCs, patrulhas, perseguição e retorno ao spawn

use super::creature_move::CreatureMoveController;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NpcMoveState {
    Idle,
    Patrolling,
    Chasing,
    Returning,
}

#[derive(Debug, Clone)]
pub struct NpcMoveController {
    pub creature_move: CreatureMoveController,
    pub spawn_x: f32,
    pub spawn_y: f32,
    pub spawn_z: f32,
    pub state: NpcMoveState,
    pub waypoints: Vec<(f32, f32, f32)>,
    pub current_waypoint_idx: usize,
}

impl NpcMoveController {
    pub fn new(x: f32, y: f32, z: f32, heading: u8, speed: f32) -> Self {
        Self {
            creature_move: CreatureMoveController::new(x, y, z, heading, speed),
            spawn_x: x,
            spawn_y: y,
            spawn_z: z,
            state: NpcMoveState::Idle,
            waypoints: Vec::new(),
            current_waypoint_idx: 0,
        }
    }

    pub fn start_chase(&mut self) {
        self.state = NpcMoveState::Chasing;
        self.creature_move.is_moving = true;
    }

    pub fn start_return(&mut self) {
        self.state = NpcMoveState::Returning;
        self.creature_move.is_moving = true;
    }

    pub fn step_towards(&mut self, target_x: f32, target_y: f32, target_z: f32, dt: f32) -> bool {
        let dist = self.creature_move.distance_to(target_x, target_y, target_z);
        let step_dist = self.creature_move.speed * dt;

        if dist <= step_dist {
            self.creature_move.set_position(target_x, target_y, target_z, self.creature_move.heading);
            if self.state == NpcMoveState::Returning {
                self.state = NpcMoveState::Idle;
                self.creature_move.is_moving = false;
            }
            true // Chegou ao destino
        } else {
            let ratio = step_dist / dist;
            let nx = self.creature_move.x + (target_x - self.creature_move.x) * ratio;
            let ny = self.creature_move.y + (target_y - self.creature_move.y) * ratio;
            let nz = self.creature_move.z + (target_z - self.creature_move.z) * ratio;
            self.creature_move.set_position(nx, ny, nz, self.creature_move.heading);
            false
        }
    }
}
