//! Controlador de Movimento de Entidades Controláveis (PlayableMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct PlayableMoveController {
    pub base: CreatureMoveController,
    pub target_dest: Option<Coord>,
}

impl PlayableMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(position, heading, speed),
            target_dest: None,
        }
    }

    pub fn set_target_destination(&mut self, dest: Coord) {
        self.target_dest = Some(dest);
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
        self.target_dest = None;
    }
}

impl MoveController for PlayableMoveController {
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
