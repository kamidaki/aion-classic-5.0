//! Pacote SM_PUT_OBJECT

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmPutObject {
    pub object_id: u32,
    pub name: String,
    pub pos: Coord,
}
