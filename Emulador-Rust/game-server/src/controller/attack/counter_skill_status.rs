//! Status de Habilidade de Contra-Ataque (CounterSkillStatus - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum CounterSkillStatus {
    #[default]
    None,
    Dodge,
    Parry,
    Block,
    Resist,
}
