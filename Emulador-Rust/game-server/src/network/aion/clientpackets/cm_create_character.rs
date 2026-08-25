//! Pacote CM_CREATE_CHARACTER (Opcode 0x00C7)

#[derive(Debug, Clone)]
pub struct CmCreateCharacter {
    pub name: String,
    pub class_id: u8,
    pub race_id: u8,
    pub gender_id: u8,
    pub appearance_data: Vec<u8>,
}
