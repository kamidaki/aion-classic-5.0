//! Pacotes Client de Comércio, Broker e Trocas (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BuySell {
    pub npc_obj_id: u32,
    pub trade_action: u8,
    pub item_id: u32,
    pub count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GlobalTradeRegister {
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub count: u32,
    pub price_per_piece: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GlobalTradeSaleslog {
    pub item_template_id: u32,
    pub quality: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GlobalTradeBuy {
    pub listing_id: u32,
    pub item_template_id: u32,
    pub count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GlobalTradeAvgPrice {
    pub item_template_id: u32,
}
