//! Pacote SM_HIT_POINT (Opcode 0x000F)

#[derive(Debug, Clone)]
pub struct SmHitPoint {
    pub cur_hp: i32,
    pub max_hp: i32,
}
