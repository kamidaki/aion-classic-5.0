use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BrokerRace {
    Elyos,
    Asmodian,
}

#[derive(Debug, Clone)]
pub struct BrokerItem {
    pub item_unique_id: u32,
    pub item_id: u32,
    pub item_count: u32,
    pub price: u64,
    pub seller_id: u32,
    pub seller_name: String,
    pub is_sold: bool,
    pub is_settled: bool,
    pub registered_time_sec: u64,
    pub broker_race: BrokerRace,
}

impl BrokerItem {
    pub fn new(
        item_unique_id: u32,
        item_id: u32,
        item_count: u32,
        price: u64,
        seller_id: u32,
        seller_name: String,
        broker_race: BrokerRace,
    ) -> Self {
        let registered_time_sec = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        Self {
            item_unique_id,
            item_id,
            item_count,
            price,
            seller_id,
            seller_name,
            is_sold: false,
            is_settled: false,
            registered_time_sec,
            broker_race,
        }
    }

    /// Expiracao padrao de 8 dias no Aion
    pub fn is_expired(&self, current_time_sec: u64) -> bool {
        const EIGHT_DAYS_SEC: u64 = 8 * 24 * 3600;
        current_time_sec.saturating_sub(self.registered_time_sec) > EIGHT_DAYS_SEC
    }
}

#[derive(Debug, Clone, Default)]
pub struct BrokerService {
    pub items: HashMap<u32, BrokerItem>,
    next_id: u32,
}

impl BrokerService {
    pub const REGISTRATION_FEE_PERCENT: f64 = 0.02; // 2% taxa de registro
    pub const SALES_FEE_PERCENT: f64 = 0.02; // 2% taxa de venda

    pub fn new() -> Self {
        Self {
            items: HashMap::new(),
            next_id: 1,
        }
    }

    pub fn register_item(
        &mut self,
        item_id: u32,
        item_count: u32,
        price: u64,
        seller_id: u32,
        seller_name: String,
        broker_race: BrokerRace,
    ) -> (u32, u64) {
        let id = self.next_id;
        self.next_id = self.next_id.wrapping_add(1);

        let fee = ((price as f64) * Self::REGISTRATION_FEE_PERCENT).ceil() as u64;
        let fee = fee.max(10); // Taxa minima de 10 Kinah

        let item = BrokerItem::new(
            id,
            item_id,
            item_count,
            price,
            seller_id,
            seller_name,
            broker_race,
        );
        self.items.insert(id, item);
        (id, fee)
    }

    pub fn search_items(
        &self,
        broker_race: BrokerRace,
        start_page: usize,
        page_size: usize,
    ) -> (Vec<BrokerItem>, usize) {
        let active: Vec<BrokerItem> = self
            .items
            .values()
            .filter(|i| i.broker_race == broker_race && !i.is_sold && !i.is_settled)
            .cloned()
            .collect();

        let total = active.len();
        let skip = start_page * page_size;
        let page_items = active.into_iter().skip(skip).take(page_size).collect();
        (page_items, total)
    }

    pub fn buy_item(
        &mut self,
        broker_item_id: u32,
        buyer_id: u32,
        buyer_kinah: u64,
    ) -> Result<(u32, u32, u64, u32, u64), &'static str> {
        let item = self.items.get_mut(&broker_item_id).ok_or("Item nao encontrado")?;
        if item.is_sold || item.is_settled {
            return Err("Item ja vendido ou finalizado");
        }
        if item.seller_id == buyer_id {
            return Err("Voce nao pode comprar seu proprio item");
        }
        if buyer_kinah < item.price {
            return Err("Kinah insuficiente");
        }

        item.is_sold = true;
        let sales_cut = ((item.price as f64) * (1.0 - Self::SALES_FEE_PERCENT)) as u64;

        Ok((
            item.item_id,
            item.item_count,
            item.price,
            item.seller_id,
            sales_cut,
        ))
    }

    pub fn cancel_listing(&mut self, broker_item_id: u32, seller_id: u32) -> Result<(u32, u32), &'static str> {
        let item = self.items.get_mut(&broker_item_id).ok_or("Item nao encontrado")?;
        if item.seller_id != seller_id {
            return Err("Item pertence a outro jogador");
        }
        if item.is_sold {
            return Err("Item ja vendido");
        }
        let res = (item.item_id, item.item_count);
        self.items.remove(&broker_item_id);
        Ok(res)
    }

    pub fn settle_seller_proceeds(&mut self, seller_id: u32) -> u64 {
        let mut total_payout = 0u64;
        for item in self.items.values_mut() {
            if item.seller_id == seller_id && item.is_sold && !item.is_settled {
                item.is_settled = true;
                let payout = ((item.price as f64) * (1.0 - Self::SALES_FEE_PERCENT)) as u64;
                total_payout += payout;
            }
        }
        total_payout
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_broker_lifecycle() {
        let mut broker = BrokerService::new();

        // 1. Registro
        let (id, fee) = broker.register_item(
            182000001,
            5,
            100_000,
            101,
            "SellerDev".to_string(),
            BrokerRace::Elyos,
        );
        assert_eq!(fee, 2000); // 2% de 100k

        // 2. Busca
        let (results, total) = broker.search_items(BrokerRace::Elyos, 0, 10);
        assert_eq!(total, 1);
        assert_eq!(results[0].item_id, 182000001);

        // 3. Compra
        let buy_res = broker.buy_item(id, 202, 150_000).expect("deve comprar");
        assert_eq!(buy_res.0, 182000001);
        assert_eq!(buy_res.1, 5);
        assert_eq!(buy_res.2, 100_000);
        assert_eq!(buy_res.3, 101);
        assert_eq!(buy_res.4, 98_000); // 100k - 2% fee

        // 4. Liquidacao pelo vendedor
        let payout = broker.settle_seller_proceeds(101);
        assert_eq!(payout, 98_000);
    }
}
