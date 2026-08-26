//! Controlador de Movimento de Invocações de Spiritmaster (SummonMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SummonMoveController {
    pub base: CreatureMoveController,
    pub follow_target: Option<Coord>,
}

impl SummonMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(position, heading, speed),
            follow_target: None,
        }
    }

    pub fn set_follow_target(&mut self, target: Coord) {
        self.follow_target = Some(target);
        self.base.is_moving = true;
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
        self.follow_target = None;
    }
}

impl MoveController for SummonMoveController {
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
