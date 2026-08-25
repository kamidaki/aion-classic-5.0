use std::collections::HashMap;

/// Item oferecido numa sessao de troca P2P
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TradeItem {
    pub item_id: u32,
    pub count: u32,
}

/// Estado da sessao de troca P2P entre dois jogadores
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TradeState {
    Active,
    Locked,
    Confirmed,
}

/// Sessao de troca segura 1v1 (P2P Exchange)
#[derive(Debug, Clone)]
pub struct P2PTradeSession {
    pub player_a: u32,
    pub player_b: u32,
    pub items_a: Vec<TradeItem>,
    pub items_b: Vec<TradeItem>,
    pub kinah_a: u64,
    pub kinah_b: u64,
    pub state_a: TradeState,
    pub state_b: TradeState,
}

impl P2PTradeSession {
    pub fn new(player_a: u32, player_b: u32) -> Self {
        Self {
            player_a,
            player_b,
            items_a: Vec::new(),
            items_b: Vec::new(),
            kinah_a: 0,
            kinah_b: 0,
            state_a: TradeState::Active,
            state_b: TradeState::Active,
        }
    }

    pub fn add_item_a(&mut self, item_id: u32, count: u32) -> Result<(), &'static str> {
        if self.state_a != TradeState::Active {
            return Err("Troca ja bloqueada/confirmada");
        }
        self.items_a.push(TradeItem { item_id, count });
        Ok(())
    }

    pub fn add_item_b(&mut self, item_id: u32, count: u32) -> Result<(), &'static str> {
        if self.state_b != TradeState::Active {
            return Err("Troca ja bloqueada/confirmada");
        }
        self.items_b.push(TradeItem { item_id, count });
        Ok(())
    }

    pub fn set_kinah_a(&mut self, kinah: u64) -> Result<(), &'static str> {
        if self.state_a != TradeState::Active {
            return Err("Troca ja bloqueada/confirmada");
        }
        self.kinah_a = kinah;
        Ok(())
    }

    pub fn set_kinah_b(&mut self, kinah: u64) -> Result<(), &'static str> {
        if self.state_b != TradeState::Active {
            return Err("Troca ja bloqueada/confirmada");
        }
        self.kinah_b = kinah;
        Ok(())
    }

    pub fn lock_a(&mut self) {
        self.state_a = TradeState::Locked;
    }

    pub fn lock_b(&mut self) {
        self.state_b = TradeState::Locked;
    }

    pub fn confirm_a(&mut self) -> bool {
        if (self.state_a == TradeState::Locked || self.state_a == TradeState::Confirmed)
            && (self.state_b == TradeState::Locked || self.state_b == TradeState::Confirmed)
        {
            self.state_a = TradeState::Confirmed;
        }
        self.is_both_confirmed()
    }

    pub fn confirm_b(&mut self) -> bool {
        if (self.state_a == TradeState::Locked || self.state_a == TradeState::Confirmed)
            && (self.state_b == TradeState::Locked || self.state_b == TradeState::Confirmed)
        {
            self.state_b = TradeState::Confirmed;
        }
        self.is_both_confirmed()
    }

    pub fn is_both_confirmed(&self) -> bool {
        self.state_a == TradeState::Confirmed && self.state_b == TradeState::Confirmed
    }
}

/// Gerenciador de Lojas de NPCs e Trocas
#[derive(Debug, Clone, Default)]
pub struct TradeService {
    pub active_p2p_trades: HashMap<u32, P2PTradeSession>,
    /// Preco base de compra e venda em NPCs: (preco_compra, preco_venda)
    pub npc_item_prices: HashMap<u32, (u64, u64)>,
    /// Catálogo de mercadorias vendidas por lista de NPC
    pub goods_lists: HashMap<u32, Vec<String>>,
}

impl TradeService {
    pub fn new() -> Self {
        let mut npc_item_prices = HashMap::new();
        // Itens consumiveis basicos padrao
        npc_item_prices.insert(160000001, (100, 15)); // Minor Recovery Potion
        npc_item_prices.insert(160000002, (250, 35)); // Lesser Recovery Potion
        npc_item_prices.insert(162000001, (50, 8));   // Minor Mana Potion
        npc_item_prices.insert(162000002, (150, 20));  // Lesser Mana Potion
        Self {
            active_p2p_trades: HashMap::new(),
            npc_item_prices,
            goods_lists: HashMap::new(),
        }
    }

    pub fn from_data(data_goods: &HashMap<u32, crate::data_loader::GoodsListDef>) -> Self {
        let mut s = Self::new();
        for (id, def) in data_goods {
            s.goods_lists.insert(*id, def.items.clone());
        }
        s
    }

    pub fn buy_from_npc(
        &self,
        player_kinah: u64,
        item_id: u32,
        count: u32,
    ) -> Result<(u64, u64), &'static str> {
        let (buy_price, _) = self
            .npc_item_prices
            .get(&item_id)
            .copied()
            .unwrap_or((1000, 100)); // Preco padrao se nao cadastrado

        let total_cost = buy_price.saturating_mul(count as u64);
        if player_kinah < total_cost {
            return Err("Kinah insuficiente para compra no NPC");
        }
        let remaining_kinah = player_kinah - total_cost;
        Ok((total_cost, remaining_kinah))
    }

    pub fn sell_to_npc(
        &self,
        player_kinah: u64,
        item_id: u32,
        count: u32,
    ) -> (u64, u64) {
        let (_, sell_price) = self
            .npc_item_prices
            .get(&item_id)
            .copied()
            .unwrap_or((100, 15));

        let payout = sell_price.saturating_mul(count as u64);
        let new_kinah = player_kinah.saturating_add(payout);
        (payout, new_kinah)
    }

    pub fn start_p2p_trade(&mut self, player_a: u32, player_b: u32) {
        let session = P2PTradeSession::new(player_a, player_b);
        self.active_p2p_trades.insert(player_a, session.clone());
        self.active_p2p_trades.insert(player_b, session);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_npc_trade() {
        let service = TradeService::new();
        let (cost, remaining) = service
            .buy_from_npc(5000, 160000001, 10)
            .expect("deve comprar");
        assert_eq!(cost, 1000);
        assert_eq!(remaining, 4000);

        let (payout, new_kinah) = service.sell_to_npc(remaining, 160000001, 5);
        assert_eq!(payout, 75);
        assert_eq!(new_kinah, 4075);
    }

    #[test]
    fn test_p2p_exchange_flow() {
        let mut session = P2PTradeSession::new(101, 202);
        assert_eq!(session.state_a, TradeState::Active);

        session.add_item_a(10000001, 1).unwrap();
        session.set_kinah_b(50_000).unwrap();

        session.lock_a();
        session.lock_b();

        assert!(!session.confirm_a());
        assert!(session.confirm_b());
        assert!(session.is_both_confirmed());
    }
}
