//! VisibleObjectController - Gerenciador básico de objetos visíveis no mundo

#[derive(Debug, Clone)]
pub struct VisibleObjectController {
    pub object_id: u32,
    pub map_id: u32,
    pub is_spawned: bool,
}

impl VisibleObjectController {
    pub fn new(object_id: u32, map_id: u32) -> Self {
        Self {
            object_id,
            map_id,
            is_spawned: false,
        }
    }

    pub fn spawn(&mut self) {
        self.is_spawned = true;
    }

    pub fn despawn(&mut self) {
        self.is_spawned = false;
    }

    pub fn is_visible(&self) -> bool {
        self.is_spawned
    }
}
