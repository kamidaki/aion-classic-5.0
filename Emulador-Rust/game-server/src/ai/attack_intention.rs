//! Intenções de Ataque da IA (AttackIntention - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AttackIntention {
    #[default]
    PhysicalAttack,
    SkillAttack,
    FinishAttack,
    SwitchTarget,
}
