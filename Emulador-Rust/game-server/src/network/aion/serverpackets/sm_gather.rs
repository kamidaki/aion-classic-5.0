//! Pacote SM_GATHER

#[derive(Debug, Clone)]
pub struct SmGather {
    pub gatherable_id: u32,
    pub player_id: u32,
    pub success: bool,
}
