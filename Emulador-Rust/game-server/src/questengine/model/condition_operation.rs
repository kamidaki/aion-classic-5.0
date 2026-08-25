//! Operação de Condição de Missão (ConditionOperation - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ConditionOperation {
    #[default]
    Equal,
    NotEqual,
    Greater,
    GreaterOrEqual,
    Less,
    LessOrEqual,
    InRange,
}
