//! HouseController - Gerenciador de habitações, estúdios e mansões

#[derive(Debug, Clone)]
pub struct HouseController {
    pub house_id: u32,
    pub owner_id: Option<u32>,
    pub house_type: u8,
    pub furniture_count: u32,
    pub is_auction_active: bool,
    pub current_bid: u64,
}

impl HouseController {
    pub fn new(house_id: u32, house_type: u8) -> Self {
        Self {
            house_id,
            owner_id: None,
            house_type,
            furniture_count: 0,
            is_auction_active: false,
            current_bid: 0,
        }
    }

    pub fn place_furniture(&mut self) -> bool {
        if self.furniture_count < 100 {
            self.furniture_count += 1;
            true
        } else {
            false
        }
    }

    pub fn start_auction(&mut self, base_bid: u64) {
        self.is_auction_active = true;
        self.current_bid = base_bid;
    }

    pub fn bid(&mut self, player_id: u32, amount: u64) -> bool {
        if self.is_auction_active && amount > self.current_bid {
            self.current_bid = amount;
            self.owner_id = Some(player_id);
            true
        } else {
            false
        }
    }
}
