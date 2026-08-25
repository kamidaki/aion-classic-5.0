//! Pacote SM_CREATE_CHARACTER (Opcode 0x00C7)

#[derive(Debug, Clone)]
pub struct SmCreateCharacter {
    pub success: bool,
    pub player_id: u32,
}
