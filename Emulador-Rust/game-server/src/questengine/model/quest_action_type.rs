//! Tipo de Ação Disparada em Missão (QuestActionType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum QuestActionType {
    #[default]
    ActionNone,
    ActionItemUse,
    ActionGather,
    ActionLoot,
    ActionAttack,
    ActionZoneEnter,
}
