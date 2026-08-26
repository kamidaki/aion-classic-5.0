//! Objetos Estáticos do Mundo (Portas, Armadilhas, Kisks, Caixas de Correio - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::visible_object::VisibleObject;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StaticObjectType {
    Door,
    Kisk,
    Trap,
    Postbox,
    Artifact,
    Chest,
}

#[derive(Debug, Clone)]
pub struct StaticObjectModel {
    pub visible: VisibleObject,
    pub object_type: StaticObjectType,
    pub is_open_or_active: bool,
    pub owner_id: Option<u32>,
}

impl StaticObjectModel {
    pub fn new(object_id: u32, name: &str, object_type: StaticObjectType, pos: Coord, world_id: u32) -> Self {
        Self {
            visible: VisibleObject::new(object_id, name, pos, world_id, 1),
            object_type,
            is_open_or_active: true,
            owner_id: None,
        }
    }
}
