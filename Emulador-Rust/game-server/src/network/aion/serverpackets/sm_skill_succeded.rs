//! Pacote SM_SKILL_SUCCEDED

#[derive(Debug, Clone)]
pub struct SmSkillSucceded {
    pub caster_id: u32,
    pub target_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub damage: u32,
}
