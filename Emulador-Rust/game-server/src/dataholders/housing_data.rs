//! HouseDataHolder & HousingObjectDataHolder - Catálogo de Habitações e Mobílias (Housing/client_house_*.xml)

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct HouseTemplate {
    pub house_id: u32,
    pub address_name: String,
    pub house_type: u8, // 1: Studio, 2: House, 3: Mansion, 4: Estate, 5: Palace
    pub max_furniture: u32,
    pub default_fee: u64,
}

#[derive(Debug, Clone, Default)]
pub struct HouseDataHolder {
    pub houses: HashMap<u32, HouseTemplate>,
}

impl HouseDataHolder {
    pub fn new() -> Self {
        Self {
            houses: HashMap::new(),
        }
    }

    pub fn get_house(&self, house_id: u32) -> Option<&HouseTemplate> {
        self.houses.get(&house_id)
    }

    pub fn register_house(&mut self, house_id: u32, address_name: String, house_type: u8) {
        self.houses.insert(
            house_id,
            HouseTemplate {
                house_id,
                address_name,
                house_type,
                max_furniture: match house_type {
                    1 => 30,
                    2 => 50,
                    3 => 80,
                    4 => 120,
                    _ => 200,
                },
                default_fee: 100_000,
            },
        );
    }
}
