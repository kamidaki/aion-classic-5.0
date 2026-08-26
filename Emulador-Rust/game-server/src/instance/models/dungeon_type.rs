//! Tipos de Masmorras e Categorias de Grupo (DungeonType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DungeonType {
    Solo,
    Group6,
    Alliance12,
    Raid24,
    DredgionPvPvE,
    ArenaOfChaos,
    ArenaOfDiscipline,
    TiakResearchCenter,
}
