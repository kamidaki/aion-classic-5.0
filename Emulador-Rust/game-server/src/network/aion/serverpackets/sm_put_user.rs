//! Pacote SM_PUT_USER

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmPutUser {
    pub player_id: u32,
    pub name: String,
    pub pos: Coord,
    pub heading: u8,
    pub class_id: u8,
    pub race_id: u8,
    pub gender_id: u8,
    pub max_hp: i32,
    pub cur_hp: i32,
}
