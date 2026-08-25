//! Pacote SM_ATTACK (Opcode 0x0041)

#[derive(Debug, Clone)]
pub struct SmAttack {
    pub attacker_id: u32,
    pub target_id: u32,
    pub damage: u32,
    pub attack_status: u8,
}
