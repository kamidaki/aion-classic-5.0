//! Pacote SM_PUT_NPC

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmPutNpc {
    pub npc_obj_id: u32,
    pub npc_template_id: u32,
    pub pos: Coord,
    pub heading: u8,
    pub max_hp: i32,
    pub cur_hp: i32,
}
