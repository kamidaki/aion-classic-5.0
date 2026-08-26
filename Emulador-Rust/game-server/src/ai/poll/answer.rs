//! Respostas de Consultas de IA (AIAnswer - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AIAnswer {
    Positive,
    Negative,
    Custom(u32),
}

impl AIAnswer {
    pub fn is_positive(self) -> bool {
        self == Self::Positive
    }
}
