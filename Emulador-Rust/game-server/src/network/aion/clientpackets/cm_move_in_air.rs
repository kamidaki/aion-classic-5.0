//! Pacote CM_MOVE_IN_AIR

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CmMoveInAir {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub glide_flag: u8,
}
