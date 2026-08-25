//! Alcance e Formato de Alvos (TargetRange - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TargetRange {
    OnlyOne,
    Area,
    Point,
    Cone,
    Line,
}

impl Default for TargetRange {
    fn default() -> Self {
        Self::OnlyOne
    }
}
