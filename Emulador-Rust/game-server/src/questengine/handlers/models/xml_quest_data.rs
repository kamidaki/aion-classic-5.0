//! Dados de Script XML Declarativo de Missão (XmlQuestData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct XmlQuestData {
    pub quest_id: u32,
    pub start_npc_id: u32,
    pub end_npc_id: u32,
    pub script_name: String,
}

impl XmlQuestData {
    pub fn new(quest_id: u32, start_npc_id: u32, end_npc_id: u32, script_name: &str) -> Self {
        Self {
            quest_id,
            start_npc_id,
            end_npc_id,
            script_name: script_name.to_string(),
        }
    }
}
