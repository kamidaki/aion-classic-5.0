//! Objeto Visível no Mundo (VisibleObject - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::aion_object::AionObject;

#[derive(Debug, Clone)]
pub struct VisibleObject {
    pub object_id: u32,
    pub name: String,
    pub position: Coord,
    pub heading: u8,
    pub world_id: u32,
    pub instance_id: u32,
    pub target_id: Option<u32>,
}

impl VisibleObject {
    pub fn new(object_id: u32, name: &str, position: Coord, world_id: u32, instance_id: u32) -> Self {
        Self {
            object_id,
            name: name.to_string(),
            position,
            heading: 0,
            world_id,
            instance_id,
            target_id: None,
        }
    }
}

impl AionObject for VisibleObject {
    fn get_object_id(&self) -> u32 {
        self.object_id
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_position(&self) -> Coord {
        self.position
    }
}
