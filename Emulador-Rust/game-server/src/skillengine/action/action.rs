//! Trait de Ações Imediatas de Habilidade (SkillAction - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;

pub trait SkillAction: Send + Sync {
    /// Executa a ação imediata no conjurador (ex: consumir HP, MP, DP ou itens)
    fn execute(&self, caster: &mut Character) -> Result<(), &'static str>;
}
