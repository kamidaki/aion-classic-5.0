//! Tipos de NPCs (NpcType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum NpcType {
    #[default]
    Peace,
    Attackable,
    Aggressive,
    Invulnerable,
    Resurrect,
    Friend,
    Artifact,
}
