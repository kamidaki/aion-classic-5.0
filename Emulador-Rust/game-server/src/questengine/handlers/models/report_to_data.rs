//! Dados para Template de Reportar a um NPC (ReportToData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct ReportToData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
}

impl ReportToData {
    pub fn new(start_npc_id: u32, end_npc_id: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
        }
    }
}
