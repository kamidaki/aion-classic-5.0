pub mod types;
pub mod region;
pub mod zone;
pub mod objects;
pub mod environment;
pub mod map;

pub use types::{Heading, Point3D, WorldPosition};
pub use region::{Region, RegionGrid, RegionStreaming};
pub use zone::{MaterialZone, Zone, ZoneGeometry, ZoneService, ZoneType};
pub use objects::{Creature, VisibleObject};
pub use environment::{FlyRing, WeatherManager, WeatherType, WindstreamPath};
pub use map::{MapType, WorldMap, WorldMapInstance};

#[cfg(test)]
mod tests;

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use crate::geoengine::GeoEngine;

pub struct WorldService {
    maps: RwLock<HashMap<u32, Arc<WorldMap>>>,
    zone_service: Arc<ZoneService>,
    weather_manager: Arc<WeatherManager>,
    geo_engine: Arc<GeoEngine>,
}

impl WorldService {
    pub fn new(geo_engine: Arc<GeoEngine>) -> Self {
        Self {
            maps: RwLock::new(HashMap::new()),
            zone_service: Arc::new(ZoneService::new()),
            weather_manager: Arc::new(WeatherManager::new()),
            geo_engine,
        }
    }

    pub fn register_map(&self, map_id: u32, name: String, map_type: MapType, map_size: f32, fly_allowed: bool, pvp_allowed: bool) {
        let geo_map = self.geo_engine.load_world(map_id).ok();
        let world_map = Arc::new(WorldMap::new(
            map_id,
            name,
            map_type,
            map_size,
            2000,
            fly_allowed,
            pvp_allowed,
            geo_map,
        ));

        let mut maps = self.maps.write().unwrap();
        maps.insert(map_id, world_map);
    }

    pub fn get_map(&self, map_id: u32) -> Option<Arc<WorldMap>> {
        let maps = self.maps.read().unwrap();
        maps.get(&map_id).cloned()
    }

    pub fn get_instance(&self, map_id: u32, instance_id: u32) -> Option<Arc<WorldMapInstance>> {
        self.get_map(map_id).and_then(|m| m.get_instance(instance_id))
    }

    pub fn zone_service(&self) -> &Arc<ZoneService> {
        &self.zone_service
    }

    pub fn weather_manager(&self) -> &Arc<WeatherManager> {
        &self.weather_manager
    }

    pub fn geo_engine(&self) -> &Arc<GeoEngine> {
        &self.geo_engine
    }

    pub fn get_ground_z(&self, map_id: u32, x: f32, y: f32, current_z: Option<f32>) -> f32 {
        self.geo_engine.get_z(map_id, x, y, current_z)
    }

    pub fn can_see(&self, map_id: u32, start_pos: &WorldPosition, end_pos: &WorldPosition) -> bool {
        self.geo_engine.can_see(map_id, &start_pos.to_vector3f(), &end_pos.to_vector3f())
    }
}
