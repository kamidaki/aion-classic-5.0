//! Ações e Páginas de Diálogo (DialogAction / DialogPage - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum DialogAction {
    #[default]
    None,
    Buy,
    Sell,
    OpenWarehouse,
    OpenAccountWarehouse,
    QuestSelect,
    QuestAccept,
    QuestReward,
    Teleport,
    ChangeClass,
    SoulHeal,
    LegionCreate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum DialogPage {
    #[default]
    SelectAction,
    QuestList,
    TradeBuy,
    TradeSell,
    Warehouse,
    TeleportList,
    StigmaWindow,
}
