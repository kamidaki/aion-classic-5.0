//! Fases e Estágios de Masmorras (StageType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum StageType {
    #[default]
    Starting,
    Phase1,
    Phase2,
    Phase3,
    Boss,
    Complete,
    Failed,
}
