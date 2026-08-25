//! PlayableMoveController - Controle de movimentação para entidades jogáveis

use super::creature_move::CreatureMoveController;
use super::glide::GlideFlag;

#[derive(Debug, Clone)]
pub struct PlayableMoveController {
    pub creature_move: CreatureMoveController,
    pub glide_flag: GlideFlag,
    pub is_falling: bool,
    pub fall_distance: f32,
}

impl PlayableMoveController {
    pub fn new(x: f32, y: f32, z: f32, heading: u8, speed: f32) -> Self {
        Self {
            creature_move: CreatureMoveController::new(x, y, z, heading, speed),
            glide_flag: GlideFlag::None,
            is_falling: false,
            fall_distance: 0.0,
        }
    }

    pub fn update_glide(&mut self, flag: GlideFlag) {
        self.glide_flag = flag;
    }
}
