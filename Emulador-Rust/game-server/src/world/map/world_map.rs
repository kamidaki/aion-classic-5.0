use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use super::map_type::MapType;
use super::world_map_instance::WorldMapInstance;
use crate::geoengine::GeoMap;

pub struct WorldMap {
    pub map_id: u32,
    pub name: String,
    pub map_type: MapType,
    pub map_size: f32,
    pub max_players: u32,
    pub fly_allowed: bool,
    pub pvp_allowed: bool,
    pub geo_map: Option<Arc<GeoMap>>,
    pub instances: RwLock<HashMap<u32, Arc<WorldMapInstance>>>,
}

impl WorldMap {
    pub fn new(
        map_id: u32,
        name: String,
        map_type: MapType,
        map_size: f32,
        max_players: u32,
        fly_allowed: bool,
        pvp_allowed: bool,
        geo_map: Option<Arc<GeoMap>>,
    ) -> Self {
        let mut instances = HashMap::new();
        // Default instance 1
        instances.insert(
            1,
            Arc::new(WorldMapInstance::new(1, map_id, 1, map_size, 128.0)),
        );

        Self {
            map_id,
            name,
            map_type,
            map_size,
            max_players,
            fly_allowed,
            pvp_allowed,
            geo_map,
            instances: RwLock::new(instances),
        }
    }

    pub fn get_instance(&self, instance_id: u32) -> Option<Arc<WorldMapInstance>> {
        let instances = self.instances.read().unwrap();
        instances.get(&instance_id).cloned()
    }

    pub fn get_or_create_instance(&self, instance_id: u32) -> Arc<WorldMapInstance> {
        {
            let instances = self.instances.read().unwrap();
            if let Some(inst) = instances.get(&instance_id) {
                return inst.clone();
            }
        }
        let new_inst = Arc::new(WorldMapInstance::new(instance_id, self.map_id, 1, self.map_size, 128.0));
        let mut instances = self.instances.write().unwrap();
        instances.insert(instance_id, new_inst.clone());
        new_inst
    }
}
