//! Controlador de Objetos Estáticos e Interativos (StaticObjectController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum StaticObjectType {
    #[default]
    Door,
    Chest,
    Artifact,
    BindPoint,
    Kisk,
    Postbox,
}

pub struct StaticObjectController {
    pub visible: VisibleObjectController,
    pub object_type: StaticObjectType,
    pub is_open: bool,
    pub required_key_id: Option<u32>,
}

impl StaticObjectController {
    pub fn new(
        object_id: u32,
        map_id: u32,
        position: Coord,
        object_type: StaticObjectType,
        required_key_id: Option<u32>,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            object_type,
            is_open: false,
            required_key_id,
        }
    }

    pub fn use_object(&mut self, player_keys: &[u32]) -> bool {
        if let Some(req_key) = self.required_key_id {
            if !player_keys.contains(&req_key) {
                return false;
            }
        }
        self.is_open = !self.is_open;
        true
    }
}
