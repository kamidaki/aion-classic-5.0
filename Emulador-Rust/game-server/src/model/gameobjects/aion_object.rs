//! Objeto Base do Mundo de Aion (AionObject - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

pub trait AionObject: Send + Sync {
    fn get_object_id(&self) -> u32;
    fn get_name(&self) -> &str;
    fn get_position(&self) -> Coord;
}
