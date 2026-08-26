//! Controlador de Movimento do Jogador (PlayerMoveController - Padrão Java Aion Classic 2.8 / 4.5)

use super::creature_move_controller::CreatureMoveController;
use super::move_controller::MoveController;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct PlayerMoveController {
    pub base: CreatureMoveController,
    pub is_gliding: bool,
    pub is_flying: bool,
    pub glide_start_pos: Option<Coord>,
}

impl PlayerMoveController {
    pub fn new(position: Coord, heading: u8, speed: f32) -> Self {
        Self {
            base: CreatureMoveController::new(position, heading, speed),
            is_gliding: false,
            is_flying: false,
            glide_start_pos: None,
        }
    }

    pub fn start_gliding(&mut self) {
        self.is_gliding = true;
        self.glide_start_pos = Some(self.base.position);
    }

    pub fn stop_gliding(&mut self) {
        self.is_gliding = false;
        self.glide_start_pos = None;
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
        self.stop_gliding();
    }
}

impl MoveController for PlayerMoveController {
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
