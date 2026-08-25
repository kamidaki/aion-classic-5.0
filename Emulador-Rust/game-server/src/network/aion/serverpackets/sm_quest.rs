//! Pacote SM_QUEST

#[derive(Debug, Clone)]
pub struct SmQuest {
    pub quest_id: u32,
    pub status: u8,
    pub step: u32,
}
