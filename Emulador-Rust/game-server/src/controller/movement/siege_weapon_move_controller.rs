//! Controlador de Movimento de Armas de Cerco (SiegeWeaponMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SiegeWeaponMoveController {
    pub base: CreatureMoveController,
    pub is_deployed: bool,
}

impl SiegeWeaponMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(position, heading, speed),
            is_deployed: false,
        }
    }

    pub fn deploy(&mut self) {
        self.is_deployed = true;
        self.base.stop_moving();
    }

    pub fn undeploy(&mut self) {
        self.is_deployed = false;
    }

    pub fn update_position(&mut self, new_pos: Coord, heading: u8) {
        if !self.is_deployed {
            self.base.update_position(new_pos, heading);
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
    }
}

impl MoveController for SiegeWeaponMoveController {
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
