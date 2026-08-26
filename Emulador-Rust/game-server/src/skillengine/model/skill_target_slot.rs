//! Slots de Efeito e Alvos (SkillTargetSlot - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SkillTargetSlot {
    Buff,
    Debuff,
    Chant,
    Spec,
    Stigma,
    None,
}

impl Default for SkillTargetSlot {
    fn default() -> Self {
        Self::Buff
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DispelCategoryType {
    None,
    All,
    Buff,
    Debuff,
    DebuffMental,
    DebuffPhysical,
    NpcBuff,
    NpcDebuff,
    Stigma,
}

impl Default for DispelCategoryType {
    fn default() -> Self {
        Self::None
    }
}
