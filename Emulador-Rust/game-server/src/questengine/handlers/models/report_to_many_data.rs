//! Dados para Template de Reportar a Múltiplos NPCs em Sequência (ReportToManyData - Padrão Java Aion Classic 2.8 / 4.5)

use super::npc_infos::NpcInfos;

#[derive(Debug, Clone)]
pub struct ReportToManyData {
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub npc_infos: Vec<NpcInfos>,
}

impl ReportToManyData {
    pub fn new(start_npc_id: u32, end_npc_id: u32) -> Self {
        Self {
            start_npc_id,
            end_npc_id,
            npc_infos: Vec::new(),
        }
    }

    pub fn with_npc_info(mut self, info: NpcInfos) -> Self {
        self.npc_infos.push(info);
        self
    }
}
