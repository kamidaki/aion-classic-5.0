//! Pacote SM_MANA_POINT (Opcode 0x004A)

#[derive(Debug, Clone)]
pub struct SmManaPoint {
    pub cur_mp: i32,
    pub max_mp: i32,
}
