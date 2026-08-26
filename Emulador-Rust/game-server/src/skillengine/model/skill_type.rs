//! Tipos e Subtipos de Habilidade (Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SkillType {
    Physical,
    Magical,
}

impl Default for SkillType {
    fn default() -> Self {
        Self::Physical
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SkillSubType {
    None,
    Attack,
    Buff,
    Debuff,
    Heal,
    Summon,
    Trap,
    Transform,
    Special,
}

impl Default for SkillSubType {
    fn default() -> Self {
        Self::Attack
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SkillElement {
    None,
    Fire,
    Water,
    Wind,
    Earth,
    Light,
    Dark,
}

impl Default for SkillElement {
    fn default() -> Self {
        Self::None
    }
}
