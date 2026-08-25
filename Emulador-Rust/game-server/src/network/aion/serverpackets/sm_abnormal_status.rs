//! Pacote SM_ABNORMAL_STATUS

#[derive(Debug, Clone)]
pub struct SmAbnormalStatus {
    pub target_id: u32,
    pub effect_id: u32,
    pub duration_seconds: u32,
}
