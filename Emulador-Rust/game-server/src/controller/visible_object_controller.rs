//! Controlador Base de Objetos Visíveis no Mundo (VisibleObjectController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct VisibleObjectController {
    pub object_id: u32,
    pub map_id: u32,
    pub position: Coord,
    pub heading: u8,
    pub is_spawned: bool,
    pub is_in_world: bool,
}

impl VisibleObjectController {
    pub fn new(object_id: u32, map_id: u32, position: Coord, heading: u8) -> Self {
        Self {
            object_id,
            map_id,
            position,
            heading,
            is_spawned: false,
            is_in_world: false,
        }
    }

    pub fn on_spawn(&mut self) {
        self.is_spawned = true;
        self.is_in_world = true;
    }

    pub fn on_despawn(&mut self) {
        self.is_spawned = false;
        self.is_in_world = false;
    }

    pub fn on_delete(&mut self) {
        self.on_despawn();
    }
}
