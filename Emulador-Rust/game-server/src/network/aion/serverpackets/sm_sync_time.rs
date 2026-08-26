//! Pacote SM_SYNC_TIME

#[derive(Debug, Clone)]
pub struct SmSyncTime {
    pub client_time: u32,
    pub server_time: u32,
}
