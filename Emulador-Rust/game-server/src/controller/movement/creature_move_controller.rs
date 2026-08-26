//! Controlador de Movimento de Criaturas (CreatureMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::move_controller::MoveController;
use super::movement_mask::MovementMask;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CreatureMoveController {
    pub position: Coord,
    pub heading: u8,
    pub mask: MovementMask,
    pub speed: f32,
    pub is_moving: bool,
}

impl CreatureMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            position,
            heading,
            mask: MovementMask::default(),
            speed,
            is_moving: false,
        }
    }

    pub fn update_position(&mut self, new_pos: Coord, heading: u8) {
        self.position = new_pos;
        self.heading = heading;
        self.is_moving = true;
    }

    pub fn get_position(&self) -> Coord {
        self.position
    }

    pub fn get_heading(&self) -> u8 {
        self.heading
    }

    pub fn is_moving(&self) -> bool {
        self.is_moving
    }

    pub fn stop_moving(&mut self) {
        self.is_moving = false;
        self.mask = MovementMask(MovementMask::IMMEDIATE);
    }
}

impl MoveController for CreatureMoveController {
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
