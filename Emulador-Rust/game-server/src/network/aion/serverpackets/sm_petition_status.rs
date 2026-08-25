//! Pacote SM_PETITION_STATUS

#[derive(Debug, Clone)]
pub struct SmPetitionStatus {
    pub has_petition: bool,
    pub petition_id: u32,
}
