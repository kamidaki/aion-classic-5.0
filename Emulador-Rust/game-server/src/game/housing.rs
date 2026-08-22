//! Sistema de Habitação (Housing), Leilões e Decoração de Mobílias

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HouseType {
    Studio,
    House,
    Mansion,
    Estate,
    Palace,
}

#[derive(Debug, Clone, PartialEq)]
pub struct FurniturePlacement {
    pub id: u32,
    pub item_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub rotation: f32,
}

#[derive(Debug, Clone)]
pub struct House {
    pub house_id: u32,
    pub house_type: HouseType,
    pub address: u32,
    pub map_id: u32,
    pub owner_id: Option<u32>,
    pub maintenance_due_tick: u64,
    pub placed_furnitures: Vec<FurniturePlacement>,
    next_furniture_id: u32,
}

impl House {
    pub fn new(house_id: u32, house_type: HouseType, address: u32, map_id: u32) -> Self {
        Self {
            house_id,
            house_type,
            address,
            map_id,
            owner_id: None,
            maintenance_due_tick: 0,
            placed_furnitures: Vec::new(),
            next_furniture_id: 1,
        }
    }

    pub fn assign_owner(&mut self, owner_id: u32, current_tick: u64, rent_duration_ticks: u64) {
        self.owner_id = Some(owner_id);
        self.maintenance_due_tick = current_tick + rent_duration_ticks;
    }

    pub fn revoke_owner(&mut self) {
        self.owner_id = None;
        self.maintenance_due_tick = 0;
        self.placed_furnitures.clear();
    }

    pub fn place_furniture(&mut self, item_id: u32, x: f32, y: f32, z: f32, rotation: f32) -> u32 {
        let id = self.next_furniture_id;
        self.next_furniture_id += 1;

        self.placed_furnitures.push(FurniturePlacement {
            id,
            item_id,
            x,
            y,
            z,
            rotation,
        });

        id
    }

    pub fn remove_furniture(&mut self, placement_id: u32) -> bool {
        if let Some(pos) = self.placed_furnitures.iter().position(|f| f.id == placement_id) {
            self.placed_furnitures.remove(pos);
            true
        } else {
            false
        }
    }
}

#[derive(Debug, Clone)]
pub struct HousingBid {
    pub house_id: u32,
    pub top_bidder_id: Option<u32>,
    pub top_bid_kinah: u64,
    pub bids_count: u32,
    pub end_tick: u64,
}

impl HousingBid {
    pub fn new(house_id: u32, starting_bid: u64, end_tick: u64) -> Self {
        Self {
            house_id,
            top_bidder_id: None,
            top_bid_kinah: starting_bid,
            bids_count: 0,
            end_tick,
        }
    }

    pub fn place_bid(&mut self, player_id: u32, bid_amount: u64) -> bool {
        if bid_amount > self.top_bid_kinah {
            self.top_bid_kinah = bid_amount;
            self.top_bidder_id = Some(player_id);
            self.bids_count += 1;
            true
        } else {
            false
        }
    }

    pub fn resolve_auction(&self, current_tick: u64) -> Option<u32> {
        if current_tick >= self.end_tick {
            self.top_bidder_id
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn house_assignment_and_furniture_placement() {
        let mut house = House::new(101, HouseType::House, 1, 700010000);
        assert_eq!(house.owner_id, None);

        house.assign_owner(50, 100, 10000);
        assert_eq!(house.owner_id, Some(50));
        assert_eq!(house.maintenance_due_tick, 10100);

        let f_id = house.place_furniture(180000001, 10.0, 15.0, 0.0, 90.0);
        assert_eq!(house.placed_furnitures.len(), 1);
        assert_eq!(house.placed_furnitures[0].id, f_id);

        assert!(house.remove_furniture(f_id));
        assert_eq!(house.placed_furnitures.len(), 0);

        house.revoke_owner();
        assert_eq!(house.owner_id, None);
    }

    #[test]
    fn housing_bid_auction_resolution() {
        let mut auction = HousingBid::new(101, 1_000_000, 500);

        // Lower bid rejected
        assert!(!auction.place_bid(1, 900_000));

        // Valid bid
        assert!(auction.place_bid(1, 1_500_000));
        assert_eq!(auction.top_bidder_id, Some(1));
        assert_eq!(auction.top_bid_kinah, 1_500_000);

        // Higher bid outbids
        assert!(auction.place_bid(2, 2_000_000));
        assert_eq!(auction.top_bidder_id, Some(2));
        assert_eq!(auction.top_bid_kinah, 2_000_000);

        // Auction still running at tick 300
        assert_eq!(auction.resolve_auction(300), None);

        // Auction resolved at tick 500
        assert_eq!(auction.resolve_auction(500), Some(2));
    }
}
