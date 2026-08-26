//! Pacote SM_MOVE_NEW (Opcode 0x0030)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmMoveNew {
    pub object_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub move_type: u8,
}

impl SmMoveNew {
    pub fn get_coord(&self) -> Coord {
        Coord::new(self.x, self.y, self.z)
    }
}
