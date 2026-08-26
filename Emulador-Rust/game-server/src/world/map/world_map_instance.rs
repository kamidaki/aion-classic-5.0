use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use crate::world::objects::VisibleObject;
use crate::world::region::RegionGrid;
use crate::world::types::WorldPosition;

pub struct WorldMapInstance {
    pub instance_id: u32,
    pub map_id: u32,
    pub channel_id: u32,
    pub region_grid: Arc<RegionGrid>,
    pub entities: RwLock<HashMap<u32, Arc<RwLock<dyn VisibleObject>>>>,
}

impl WorldMapInstance {
    pub fn new(instance_id: u32, map_id: u32, channel_id: u32, map_size: f32, cell_size: f32) -> Self {
        let region_grid = Arc::new(RegionGrid::new(map_id, map_size, cell_size));
        Self {
            instance_id,
            map_id,
            channel_id,
            region_grid,
            entities: RwLock::new(HashMap::new()),
        }
    }

    pub fn spawn_entity(&self, entity: Arc<RwLock<dyn VisibleObject>>) {
        let (id, pos) = {
            let mut guard = entity.write().unwrap();
            guard.set_spawned(true);
            (guard.get_object_id(), guard.get_position())
        };

        if let Some(region) = self.region_grid.get_region_at(pos.x, pos.y) {
            region.add_npc(id);
        }

        let mut entities = self.entities.write().unwrap();
        entities.insert(id, entity);
    }

    pub fn despawn_entity(&self, object_id: u32) {
        let mut entities = self.entities.write().unwrap();
        if let Some(entity) = entities.remove(&object_id) {
            let mut guard = entity.write().unwrap();
            guard.set_spawned(false);
            let pos = guard.get_position();
            if let Some(region) = self.region_grid.get_region_at(pos.x, pos.y) {
                region.remove_npc(object_id);
                region.remove_player(object_id);
            }
        }
    }

    pub fn update_entity_position(&self, object_id: u32, old_pos: &WorldPosition, new_pos: &WorldPosition) {
        let old_rid = self.region_grid.get_region_id(old_pos.x, old_pos.y);
        let new_rid = self.region_grid.get_region_id(new_pos.x, new_pos.y);

        if old_rid != new_rid {
            if let Some(old_region) = self.region_grid.get_region(old_rid) {
                old_region.remove_player(object_id);
                old_region.remove_npc(object_id);
            }
            if let Some(new_region) = self.region_grid.get_region(new_rid) {
                new_region.add_player(object_id);
            }
        }
    }
}
