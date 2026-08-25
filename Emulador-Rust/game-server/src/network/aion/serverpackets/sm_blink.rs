//! Pacote SM_BLINK

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmBlink {
    pub object_id: u32,
    pub pos: Coord,
}
