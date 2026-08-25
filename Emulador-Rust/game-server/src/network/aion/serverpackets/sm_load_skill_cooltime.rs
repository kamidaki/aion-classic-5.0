//! Pacote SM_LOAD_SKILL_COOLTIME

#[derive(Debug, Clone)]
pub struct SmLoadSkillCooltime {
    pub cooldowns: Vec<(u32, u32)>, // (skill_id, remaining_ms)
}
