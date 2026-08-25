//! Pacote SM_DELETE_CHARACTER (Opcode 0x00BA)

#[derive(Debug, Clone)]
pub struct SmDeleteCharacter {
    pub success: bool,
    pub player_id: u32,
}
