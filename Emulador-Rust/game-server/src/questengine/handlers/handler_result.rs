//! Resultado da Execução de um Handler de Missão (HandlerResult - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum HandlerResult {
    #[default]
    Unknown,
    Success,
    Failed,
}

impl HandlerResult {
    pub fn is_success(&self) -> bool {
        matches!(self, Self::Success)
    }

    pub fn is_failed(&self) -> bool {
        matches!(self, Self::Failed)
    }
}
