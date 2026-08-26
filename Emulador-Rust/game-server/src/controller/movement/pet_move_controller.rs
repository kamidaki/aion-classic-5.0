//! Controlador de Movimento de Mascotes / Pets (PetMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct PetMoveController {
    pub base: CreatureMoveController,
    pub master_pos: Option<Coord>,
    pub follow_distance: f32,
}

impl PetMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(position, heading, speed),
            master_pos: None,
            follow_distance: 3.0,
        }
    }

    pub fn update_master_position(&mut self, master_pos: Coord) {
        self.master_pos = Some(master_pos);
        if self.base.position.distance(&master_pos) > self.follow_distance {
            self.base.is_moving = true;
        } else {
            self.base.is_moving = false;
        }
    }

    pub fn update_position(&mut self, new_pos: Coord, heading: u8) {
        self.base.update_position(new_pos, heading);
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
    }
}

impl MoveController for PetMoveController {
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
