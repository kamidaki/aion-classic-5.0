//! Dados de Habilidade Requisitada por Missão (QuestSkillData - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct QuestSkillData {
    pub skill_id: u32,
    pub skill_level: u8,
}

impl QuestSkillData {
    pub fn new(skill_id: u32, skill_level: u8) -> Self {
        Self {
            skill_id,
            skill_level,
        }
    }
}
