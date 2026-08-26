//! Verificador de Zona Geográfica de Missão (ZoneChecker)

#[derive(Debug, Clone)]
pub struct ZoneChecker {
    pub zone_id: u32,
}

impl ZoneChecker {
    pub fn new(zone_id: u32) -> Self {
        Self { zone_id }
    }

    pub fn is_in_zone(&self, current_zone_id: u32) -> bool {
        self.zone_id == current_zone_id
    }
}
