//! FlyPathDataHolder & WindstreamDataHolder - Rotas de Voo e Correntes de Vento

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct FlightRoute {
    pub flight_id: u32,
    pub start_point: (f32, f32, f32),
    pub end_point: (f32, f32, f32),
    pub required_kinah: u64,
    pub required_level: u8,
}

#[derive(Debug, Clone, Default)]
pub struct FlyPathDataHolder {
    pub routes: HashMap<u32, FlightRoute>,
}

impl FlyPathDataHolder {
    pub fn new() -> Self {
        Self {
            routes: HashMap::new(),
        }
    }

    pub fn get_route(&self, flight_id: u32) -> Option<&FlightRoute> {
        self.routes.get(&flight_id)
    }

    pub fn register_route(&mut self, flight_id: u32, start: (f32, f32, f32), end: (f32, f32, f32), kinah: u64, level: u8) {
        self.routes.insert(
            flight_id,
            FlightRoute {
                flight_id,
                start_point: start,
                end_point: end,
                required_kinah: kinah,
                required_level: level,
            },
        );
    }
}
