use std::collections::HashMap;
use std::sync::RwLock;
use super::zone::Zone;
use super::zone_type::ZoneType;

#[derive(Default)]
pub struct ZoneService {
    zones: RwLock<HashMap<u32, Vec<Zone>>>,
}

impl ZoneService {
    pub fn new() -> Self {
        Self {
            zones: RwLock::new(HashMap::new()),
        }
    }

    pub fn register_zone(&self, zone: Zone) {
        let mut zones_guard = self.zones.write().unwrap();
        zones_guard.entry(zone.map_id).or_default().push(zone);
    }

    pub fn get_active_zones(&self, map_id: u32, x: f32, y: f32, z: f32) -> Vec<Zone> {
        let zones_guard = self.zones.read().unwrap();
        if let Some(map_zones) = zones_guard.get(&map_id) {
            let mut matching: Vec<Zone> = map_zones
                .iter()
                .filter(|zone| zone.contains(x, y, z))
                .cloned()
                .collect();
            matching.sort_by(|a, b| b.priority.cmp(&a.priority));
            matching
        } else {
            Vec::new()
        }
    }

    pub fn is_in_zone(&self, map_id: u32, x: f32, y: f32, z: f32, zone_type: ZoneType) -> bool {
        let zones_guard = self.zones.read().unwrap();
        if let Some(map_zones) = zones_guard.get(&map_id) {
            map_zones.iter().any(|zone| zone.zone_type == zone_type && zone.contains(x, y, z))
        } else {
            false
        }
    }

    pub fn is_fly_allowed(&self, map_id: u32, x: f32, y: f32, z: f32, map_fly_default: bool) -> bool {
        if self.is_in_zone(map_id, x, y, z, ZoneType::NoFly) {
            return false;
        }
        if self.is_in_zone(map_id, x, y, z, ZoneType::Fly) {
            return true;
        }
        map_fly_default
    }

    pub fn is_pvp_allowed(&self, map_id: u32, x: f32, y: f32, z: f32, map_pvp_default: bool) -> bool {
        if self.is_in_zone(map_id, x, y, z, ZoneType::Safe) {
            return false;
        }
        if self.is_in_zone(map_id, x, y, z, ZoneType::Pvp) {
            return true;
        }
        map_pvp_default
    }
}
