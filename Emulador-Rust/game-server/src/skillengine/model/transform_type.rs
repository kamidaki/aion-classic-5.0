//! Tipos de Transformação (TransformType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TransformType {
    None,
    Avatar,
    Monster,
    Form,
    Polymorph,
}

impl Default for TransformType {
    fn default() -> Self {
        Self::None
    }
}
