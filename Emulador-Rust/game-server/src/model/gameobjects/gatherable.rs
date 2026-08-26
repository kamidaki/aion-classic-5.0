//! Modelo de Recursos Coletáveis (GatherableModel - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::visible_object::VisibleObject;

#[derive(Debug, Clone)]
pub struct GatherableModel {
    pub visible: VisibleObject,
    pub material_id: u32,
    pub skill_level_required: u32,
    pub harvest_count_left: u32,
    pub max_harvest_count: u32,
    pub respawn_time_seconds: u32,
}

impl GatherableModel {
    pub fn new(
        object_id: u32,
        name: &str,
        material_id: u32,
        pos: Coord,
        world_id: u32,
        skill_level: u32,
        harvest_count: u32,
    ) -> Self {
        Self {
            visible: VisibleObject::new(object_id, name, pos, world_id, 1),
            material_id,
            skill_level_required: skill_level,
            harvest_count_left: harvest_count,
            max_harvest_count: harvest_count,
            respawn_time_seconds: 120,
        }
    }

    pub fn harvest(&mut self) -> bool {
        if self.harvest_count_left > 0 {
            self.harvest_count_left -= 1;
            true
        } else {
            false
        }
    }
}
