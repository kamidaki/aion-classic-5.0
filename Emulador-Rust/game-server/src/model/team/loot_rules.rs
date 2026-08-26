//! Regras de Distribuição de Loot em Grupo (LootRuleType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum LootRuleType {
    #[default]
    FreeForAll,
    RoundRobin,
    Leader,
    Dice,
    Bid,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum LootThreshold {
    #[default]
    Common,
    Superior,
    Heroic,
    Fabled,
    Eternal,
    Mythic,
}
