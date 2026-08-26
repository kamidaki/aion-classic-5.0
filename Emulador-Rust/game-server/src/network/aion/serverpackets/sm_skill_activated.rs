//! Pacote SM_SKILL_ACTIVATED

#[derive(Debug, Clone)]
pub struct SmSkillActivated {
    pub skill_id: u32,
    pub active: bool,
}
