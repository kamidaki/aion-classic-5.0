//! Pacote CM_DELETE_CHARACTER (Opcode 0x00BA)

#[derive(Debug, Clone)]
pub struct CmDeleteCharacter {
    pub player_id: u32,
}
