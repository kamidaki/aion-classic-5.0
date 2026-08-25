use super::visible_object::VisibleObject;
use crate::world::types::{Heading, WorldPosition};

#[derive(Debug, Clone)]
pub struct Creature {
    pub object_id: u32,
    pub name: String,
    pub level: u8,
    pub position: WorldPosition,
    pub target_id: Option<u32>,
    pub is_spawned: bool,
    pub hp: u32,
    pub max_hp: u32,
    pub mp: u32,
    pub max_mp: u32,
    pub speed: f32,
}

impl Creature {
    pub fn new(object_id: u32, name: String, level: u8, position: WorldPosition) -> Self {
        Self {
            object_id,
            name,
            level,
            position,
            target_id: None,
            is_spawned: false,
            hp: 100,
            max_hp: 100,
            mp: 100,
            max_mp: 100,
            speed: 6.0,
        }
    }
}

impl VisibleObject for Creature {
    fn get_object_id(&self) -> u32 {
        self.object_id
    }

    fn get_position(&self) -> WorldPosition {
        self.position
    }

    fn set_position(&mut self, pos: WorldPosition) {
        self.position = pos;
    }

    fn get_heading(&self) -> Heading {
        self.position.heading
    }

    fn set_heading(&mut self, heading: Heading) {
        self.position.heading = heading;
    }

    fn get_target_id(&self) -> Option<u32> {
        self.target_id
    }

    fn set_target_id(&mut self, target_id: Option<u32>) {
        self.target_id = target_id;
    }

    fn is_spawned(&self) -> bool {
        self.is_spawned
    }

    fn set_spawned(&mut self, spawned: bool) {
        self.is_spawned = spawned;
    }
}
