//! Controlador de Movimento de NPCs e Monstros (NpcMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct NpcMoveController {
    pub base: CreatureMoveController,
    pub spawn_point: Coord,
    pub target_point: Option<Coord>,
    pub return_to_spawn: bool,
    pub is_walking: bool,
}

impl NpcMoveController {
    pub fn new(spawn_point: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(spawn_point, heading, speed),
            spawn_point,
            target_point: None,
            return_to_spawn: false,
            is_walking: true,
        }
    }

    pub fn move_to_target(&mut self, target: Coord) {
        self.target_point = Some(target);
        self.base.is_moving = true;
    }

    pub fn start_return_to_spawn(&mut self) {
        self.target_point = Some(self.spawn_point);
        self.return_to_spawn = true;
        self.base.is_moving = true;
    }

    pub fn update_position(&mut self, new_pos: Coord, heading: u8) {
        self.base.update_position(new_pos, heading);
        if let Some(dest) = self.target_point {
            if new_pos.distance(&dest) < 1.0 {
                self.stop_moving();
            }
        }
    }

    pub fn get_position(&self) -> Coord {
        self.base.get_position()
    }

    pub fn get_heading(&self) -> u8 {
        self.base.get_heading()
    }

    pub fn is_moving(&self) -> bool {
        self.base.is_moving()
    }

    pub fn stop_moving(&mut self) {
        self.base.stop_moving();
        self.target_point = None;
        self.return_to_spawn = false;
    }
}

impl MoveController for NpcMoveController {
    fn update_position(&mut self, new_pos: Coord, heading: u8) {
        self.update_position(new_pos, heading);
    }

    fn get_position(&self) -> Coord {
        self.get_position()
    }

    fn get_heading(&self) -> u8 {
        self.get_heading()
    }

    fn is_moving(&self) -> bool {
        self.is_moving()
    }

    fn stop_moving(&mut self) {
        self.stop_moving();
    }
}
