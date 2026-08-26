//! Pacote CM_PETITION

#[derive(Debug, Clone)]
pub struct CmPetition {
    pub title: String,
    pub message: String,
    pub petition_type: u8,
}
