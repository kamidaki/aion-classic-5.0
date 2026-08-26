//! Metadados e Diálogos de NPCs da Missão (NpcInfos - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct NpcInfos {
    pub npc_id: u32,
    pub quest_dialog: u32,
    pub close_dialog: u32,
}

impl NpcInfos {
    pub fn new(npc_id: u32, quest_dialog: u32, close_dialog: u32) -> Self {
        Self {
            npc_id,
            quest_dialog,
            close_dialog,
        }
    }
}
