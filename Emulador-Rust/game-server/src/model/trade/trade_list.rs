//! Listas de Comércio e Recompra (TradeList / RepurchaseList - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct TradeItemModel {
    pub item_id: u32,
    pub count: u64,
    pub price: u64,
}

#[derive(Debug, Clone, Default)]
pub struct TradeListModel {
    pub items: Vec<TradeItemModel>,
    pub required_kinah: u64,
}

#[derive(Debug, Clone, Default)]
pub struct RepurchaseListModel {
    pub items: Vec<TradeItemModel>,
}
