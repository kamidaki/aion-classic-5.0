//! Relação de Alvos (TargetRelation - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TargetRelation {
    Enemy,
    Friend,
    MyParty,
    MyAlliance,
    SelfTarget,
    All,
}

impl Default for TargetRelation {
    fn default() -> Self {
        Self::Enemy
    }
}
