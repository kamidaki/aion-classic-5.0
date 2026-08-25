//! Trait de Ações Periódicas / Ticks de Efeitos (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;

pub trait PeriodicAction: Send + Sync {
    /// Executa o tick periódico no personagem
    fn execute_tick(&self, target: &mut Character) -> Result<(), &'static str>;
}
