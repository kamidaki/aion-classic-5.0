//! Tipo de União de Condições de Missão (ConditionUnionType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ConditionUnionType {
    #[default]
    And,
    Or,
}
