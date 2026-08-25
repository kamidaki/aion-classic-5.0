use crate::world::types::{Heading, WorldPosition};

pub trait VisibleObject: Send + Sync {
    fn get_object_id(&self) -> u32;
    fn get_position(&self) -> WorldPosition;
    fn set_position(&mut self, pos: WorldPosition);
    fn get_heading(&self) -> Heading;
    fn set_heading(&mut self, heading: Heading);
    fn get_target_id(&self) -> Option<u32>;
    fn set_target_id(&mut self, target_id: Option<u32>);
    fn is_spawned(&self) -> bool;
    fn set_spawned(&mut self, spawned: bool);
}
