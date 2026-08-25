//! Pacote CM_CASTSPELL (Opcode 0x0021)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CmCastSpell {
    pub spell_id: u32,
    pub level: u8,
    pub target_type: u8,
    pub target_id: u32,
    pub target_pos: Option<Coord>,
    pub time: u32,
}
