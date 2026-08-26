//! Pacote SM_STATUS / SM_STATS_INFO (Opcode 0x00A0)

#[derive(Debug, Clone)]
pub struct SmStatus {
    pub level: u16,
    pub max_hp: i32,
    pub cur_hp: i32,
    pub max_mp: i32,
    pub cur_mp: i32,
}
