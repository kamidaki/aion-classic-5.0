//! Questões de Consulta de IA (AIQuestion - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AIQuestion {
    CanAttackPlayer,
    CanShout,
    IsImmuneToDebuff,
    ShouldDecay,
    CanThink,
    IsVisibleObject,
    CanResistAbnormal,
}
