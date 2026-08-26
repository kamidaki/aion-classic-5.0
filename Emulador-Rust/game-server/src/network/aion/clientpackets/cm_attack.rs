//! Pacote CM_ATTACK (Opcode 0x0020)

#[derive(Debug, Clone)]
pub struct CmAttack {
    pub target_id: u32,
    pub attack_type: u8,
    pub time: u32,
}
