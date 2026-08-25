//! Pacote CM_MOVE (Opcode 0x0030)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CmMove {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub move_type: u8,
}

impl CmMove {
    pub fn get_coord(&self) -> Coord {
        Coord::new(self.x, self.y, self.z)
    }
}
