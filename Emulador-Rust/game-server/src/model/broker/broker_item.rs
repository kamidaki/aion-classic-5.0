//! Modelo de Itens no Broker / Casa de Leilões (BrokerItem - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;
use crate::model::items::item::ItemModel;

#[derive(Debug, Clone)]
pub struct BrokerItemModel {
    pub item: ItemModel,
    pub price_per_unit: u64,
    pub seller_id: u32,
    pub seller_name: String,
    pub registered_time: Instant,
    pub expire_time: Instant,
}
