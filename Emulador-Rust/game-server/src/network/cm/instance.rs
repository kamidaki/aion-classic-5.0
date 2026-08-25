//! Pacotes do Cliente para Instâncias e Masmorras (CM_INSTANCE_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmInstanceInfo {
    pub player_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmInstanceLeave {
    pub instance_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmAutoGroup {
    pub instance_mask_id: u32,
    pub entry_type: u8,
}
