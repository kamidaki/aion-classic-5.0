//! Trait Base de Movimento (MoveController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

pub trait MoveController: Send + Sync {
    fn update_position(&mut self, new_pos: Coord, heading: u8);
    fn get_position(&self) -> Coord;
    fn get_heading(&self) -> u8;
    fn is_moving(&self) -> bool;
    fn stop_moving(&mut self);
}
