//! Status Crítico do Atacante (AttackerCriticalStatus - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AttackerCriticalStatus {
    #[default]
    None,
    CriticalHit,
    CriticalSkill,
}
